from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.model_config import ModelConfig
from app.schemas.model_config import (
    ModelConfigCreate,
    ModelConfigRead,
    ModelConfigTestResponse,
    ModelConfigUpdate,
)
from app.services.llm_gateway import model_config_to_read, test_model_config

router = APIRouter()


@router.get("/model-configs", response_model=list[ModelConfigRead])
def list_model_configs(
    workspace_id: str | None = None,
    organization_id: str | None = None,
    db: Session = Depends(get_db),
) -> list[dict]:
    statement = select(ModelConfig).order_by(ModelConfig.created_at.desc())
    if workspace_id:
        statement = statement.where(ModelConfig.workspace_id == workspace_id)
    if organization_id:
        statement = statement.where(ModelConfig.organization_id == organization_id)
    return [model_config_to_read(config) for config in db.scalars(statement)]


@router.post("/model-configs", response_model=ModelConfigRead)
def create_model_config(payload: ModelConfigCreate, db: Session = Depends(get_db)) -> dict:
    config = ModelConfig(**payload.model_dump())
    db.add(config)
    db.commit()
    db.refresh(config)
    return model_config_to_read(config)


@router.get("/model-configs/{config_id}", response_model=ModelConfigRead)
def get_model_config(config_id: str, db: Session = Depends(get_db)) -> dict:
    config = db.get(ModelConfig, config_id)
    if not config:
        raise HTTPException(status_code=404, detail="Model config not found")
    return model_config_to_read(config)


@router.put("/model-configs/{config_id}", response_model=ModelConfigRead)
def update_model_config(
    config_id: str,
    payload: ModelConfigUpdate,
    db: Session = Depends(get_db),
) -> dict:
    config = db.get(ModelConfig, config_id)
    if not config:
        raise HTTPException(status_code=404, detail="Model config not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(config, key, value)
    db.commit()
    db.refresh(config)
    return model_config_to_read(config)


@router.post("/model-configs/{config_id}/test", response_model=ModelConfigTestResponse)
def test_config(config_id: str, db: Session = Depends(get_db)) -> dict:
    config = db.get(ModelConfig, config_id)
    if not config:
        raise HTTPException(status_code=404, detail="Model config not found")
    try:
        return test_model_config(config)
    except ValueError as exc:
        return {
            "ok": False,
            "provider": config.provider,
            "model_name": config.model_name,
            "message": str(exc),
            "sample": None,
        }

