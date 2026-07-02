from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.knowledge import KnowledgeItem, KnowledgeSource
from app.schemas.knowledge import (
    IntelligenceCrawlRequest,
    IntelligenceCrawlResponse,
    IntelligenceDashboardRead,
    KnowledgeCrawlResponse,
    KnowledgeItemRead,
    KnowledgeSourceSeedRequest,
    KnowledgeSourceCreate,
    KnowledgeSourceRead,
    RepositoryOptionRead,
)
from app.services.agent_logger import log_agent_run
from app.services.intelligence_center import (
    REPOSITORY_OPTIONS,
    build_intelligence_dashboard,
    crawl_active_sources,
    seed_intelligence_sources,
)
from app.services.knowledge_crawler import analyze_knowledge_entry, crawl_source
from app.services.intelligence_scheduler import get_intelligence_schedule_status

router = APIRouter()


@router.get("/intelligence/repositories", response_model=list[RepositoryOptionRead])
def list_repository_options() -> list[dict]:
    return REPOSITORY_OPTIONS


@router.get("/intelligence/dashboard", response_model=IntelligenceDashboardRead)
def get_intelligence_dashboard(
    workspace_id: str | None = None,
    organization_id: str | None = None,
    db: Session = Depends(get_db),
) -> dict:
    return build_intelligence_dashboard(
        db,
        workspace_id=workspace_id,
        organization_id=organization_id,
    )


@router.get("/intelligence/schedule")
def get_intelligence_schedule() -> dict:
    return get_intelligence_schedule_status()


@router.post("/intelligence/seed-sources", response_model=list[KnowledgeSourceRead])
def seed_default_intelligence_sources(
    payload: KnowledgeSourceSeedRequest,
    db: Session = Depends(get_db),
) -> list[KnowledgeSource]:
    return seed_intelligence_sources(
        db,
        workspace_id=payload.workspace_id,
        organization_id=payload.organization_id,
        reset_existing=payload.reset_existing,
    )


@router.post("/intelligence/crawl-active", response_model=IntelligenceCrawlResponse)
def crawl_active_intelligence_sources(
    payload: IntelligenceCrawlRequest,
    db: Session = Depends(get_db),
) -> dict:
    return crawl_active_sources(
        db,
        workspace_id=payload.workspace_id,
        organization_id=payload.organization_id,
        max_sources=payload.max_sources,
    )


@router.get("/knowledge-sources", response_model=list[KnowledgeSourceRead])
def list_knowledge_sources(
    organization_id: str | None = None,
    db: Session = Depends(get_db),
) -> list[KnowledgeSource]:
    statement = select(KnowledgeSource).order_by(KnowledgeSource.created_at.desc())
    if organization_id:
        statement = statement.where(KnowledgeSource.organization_id == organization_id)
    return list(db.scalars(statement))


@router.post("/knowledge-sources", response_model=KnowledgeSourceRead)
def create_knowledge_source(
    payload: KnowledgeSourceCreate,
    db: Session = Depends(get_db),
) -> KnowledgeSource:
    source = KnowledgeSource(**payload.model_dump())
    db.add(source)
    db.commit()
    db.refresh(source)
    return source


@router.post("/knowledge-sources/{source_id}/crawl", response_model=KnowledgeCrawlResponse)
def crawl_knowledge_source(source_id: str, db: Session = Depends(get_db)) -> dict:
    source = db.get(KnowledgeSource, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Knowledge source not found")

    try:
        entries = crawl_source(source.url, source.source_type)
        items = []
        for entry in entries:
            existing = db.scalar(
                select(KnowledgeItem).where(
                    KnowledgeItem.source_id == source.id,
                    KnowledgeItem.url == entry.url,
                    KnowledgeItem.title == entry.title,
                )
            )
            if existing:
                items.append(existing)
                continue

            analysis = analyze_knowledge_entry(
                entry,
                category=source.category,
                credibility_level=source.credibility_level,
            )
            item = KnowledgeItem(
                source_id=source.id,
                organization_id=source.organization_id,
                title=entry.title[:500],
                url=entry.url,
                author=entry.author,
                published_at=entry.published_at,
                crawled_at=datetime.utcnow(),
                raw_text=entry.raw_text,
                summary=analysis["summary"],
                category=analysis["category"],
                tags=analysis["tags"],
                audiences=analysis["audiences"],
                pain_points=analysis["pain_points"],
                topic_suggestions=analysis["topic_suggestions"],
                compliance_risk=analysis["compliance_risk"],
                credibility_score=analysis["credibility_score"],
                status=analysis["status"],
            )
            db.add(item)
            items.append(item)

        source.last_crawled_at = datetime.utcnow()
        db.commit()
        for item in items:
            db.refresh(item)
        db.refresh(source)

        log_agent_run(
            db,
            agent_name="knowledge_crawler",
            workspace_id=source.workspace_id,
            organization_id=source.organization_id,
            input_payload={"source_id": source.id, "url": source.url},
            output_payload={"item_count": len(items)},
        )
        return {"source": source, "items": items, "message": f"采集完成，共处理 {len(items)} 条知识"}
    except ValueError as exc:
        log_agent_run(
            db,
            agent_name="knowledge_crawler",
            workspace_id=source.workspace_id,
            organization_id=source.organization_id,
            input_payload={"source_id": source.id, "url": source.url},
            status="failed",
            error_message=str(exc),
        )
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/knowledge-items", response_model=list[KnowledgeItemRead])
def list_knowledge_items(
    source_id: str | None = None,
    organization_id: str | None = None,
    db: Session = Depends(get_db),
) -> list[KnowledgeItem]:
    statement = select(KnowledgeItem).order_by(KnowledgeItem.crawled_at.desc())
    if source_id:
        statement = statement.where(KnowledgeItem.source_id == source_id)
    if organization_id:
        statement = statement.where(KnowledgeItem.organization_id == organization_id)
    return list(db.scalars(statement.limit(100)))
