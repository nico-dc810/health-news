from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.material import Material, MaterialChunk
from app.schemas.material import MaterialAnalyzeResponse, MaterialCreate, MaterialRead
from app.services.agent_logger import log_agent_run
from app.services.llm_agents import analyze_material_with_llm
from app.services.llm_gateway import resolve_model_config
from app.services.material_analyzer import analyze_material_text, split_chunks

router = APIRouter()


@router.get("/organizations/{organization_id}/materials", response_model=list[MaterialRead])
def list_materials(organization_id: str, db: Session = Depends(get_db)) -> list[Material]:
    statement = (
        select(Material)
        .where(Material.organization_id == organization_id)
        .order_by(Material.created_at.desc())
    )
    return list(db.scalars(statement))


@router.post("/organizations/{organization_id}/materials", response_model=MaterialRead)
def create_material(
    organization_id: str,
    payload: MaterialCreate,
    db: Session = Depends(get_db),
) -> Material:
    data = payload.model_dump()
    data["organization_id"] = organization_id
    material = Material(**data)
    db.add(material)
    db.commit()
    db.refresh(material)
    return material


@router.get("/materials/{material_id}", response_model=MaterialRead)
def get_material(material_id: str, db: Session = Depends(get_db)) -> Material:
    material = db.get(Material, material_id)
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    return material


@router.post("/materials/{material_id}/analyze", response_model=MaterialAnalyzeResponse)
def analyze_material(material_id: str, db: Session = Depends(get_db)) -> dict:
    material = db.get(Material, material_id)
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")

    model_config = resolve_model_config(
        db,
        workspace_id=material.workspace_id,
        organization_id=material.organization_id,
        use_case="material_analyzer",
    )
    if model_config and model_config.provider != "mock":
        try:
            analysis = analyze_material_with_llm(
                model_config,
                text=material.raw_text or "",
                material_type=material.material_type,
            )
        except ValueError:
            analysis = analyze_material_text(material.raw_text, material.material_type)
    else:
        analysis = analyze_material_text(material.raw_text, material.material_type)
    material.summary = analysis["summary"]
    material.structured_data = analysis
    material.tags = analysis["tags"]
    material.risk_level = analysis["risk_level"]

    for index, chunk_text in enumerate(split_chunks(material.raw_text)):
        db.add(
            MaterialChunk(
                material_id=material.id,
                chunk_index=index,
                chunk_text=chunk_text,
                summary=chunk_text[:120],
                embedding=None,
                chunk_metadata={"source": "manual_split"},
            )
        )

    db.commit()
    db.refresh(material)
    log_agent_run(
        db,
        agent_name="material_analyzer",
        workspace_id=material.workspace_id,
        organization_id=material.organization_id,
        input_payload={"material_id": material.id, "text": material.raw_text},
        output_payload=analysis,
    )
    return {"material": material, "analysis": analysis}
