from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.material import Material
from app.models.organization import Organization
from app.models.topic import Topic
from app.schemas.topic import TopicCreate, TopicGenerateRequest, TopicRead
from app.services.agent_logger import log_agent_run
from app.services.llm_agents import generate_topics_with_llm
from app.services.llm_gateway import resolve_model_config
from app.services.topic_generator import generate_topics

router = APIRouter()


@router.get("/organizations/{organization_id}/topics", response_model=list[TopicRead])
def list_topics(organization_id: str, db: Session = Depends(get_db)) -> list[Topic]:
    statement = (
        select(Topic)
        .where(Topic.organization_id == organization_id)
        .order_by(Topic.created_at.desc())
    )
    return list(db.scalars(statement))


@router.post("/organizations/{organization_id}/topics/generate", response_model=list[TopicRead])
def generate_organization_topics(
    organization_id: str,
    payload: TopicGenerateRequest,
    db: Session = Depends(get_db),
) -> list[Topic]:
    organization = db.get(Organization, organization_id)
    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found")

    materials = list(
        db.scalars(select(Material).where(Material.organization_id == organization_id).limit(20))
    )
    model_config = resolve_model_config(
        db,
        workspace_id=organization.workspace_id,
        organization_id=organization_id,
        use_case="topic_strategy",
    )
    if model_config and model_config.provider != "mock":
        try:
            generated = generate_topics_with_llm(
                model_config,
                organization_name=organization.name,
                target_audience=organization.target_audience or "未填写",
                core_services=organization.core_services or "未填写",
                material_summaries=[material.summary or material.raw_text or "" for material in materials[:8]],
                platform=payload.platform,
                conversion_goal=payload.conversion_goal,
                count=payload.count,
            )
        except ValueError:
            generated = generate_topics(
                organization,
                materials,
                platform=payload.platform,
                conversion_goal=payload.conversion_goal,
                count=payload.count,
            )
    else:
        generated = generate_topics(
            organization,
            materials,
            platform=payload.platform,
            conversion_goal=payload.conversion_goal,
            count=payload.count,
        )
    topics = []
    for item in generated["topics"]:
        topic = Topic(
            organization_id=organization_id,
            ip_profile_id=payload.ip_profile_id,
            title=item["title"],
            topic_type=item["topic_type"],
            target_audience=item["target_audience"],
            pain_point=item["pain_point"],
            platform=item["platform"],
            conversion_goal=item["conversion_goal"],
            risk_level=item["risk_level"],
            priority=item["priority"],
            source_material_ids=[material.id for material in materials],
        )
        db.add(topic)
        topics.append(topic)
    db.commit()
    for topic in topics:
        db.refresh(topic)
    log_agent_run(
        db,
        agent_name="topic_strategy",
        workspace_id=organization.workspace_id,
        organization_id=organization_id,
        input_payload=payload.model_dump(),
        retrieved_materials=[material.id for material in materials],
        output_payload=generated,
    )
    return topics


@router.post("/topics", response_model=TopicRead)
def create_topic(payload: TopicCreate, db: Session = Depends(get_db)) -> Topic:
    topic = Topic(**payload.model_dump())
    db.add(topic)
    db.commit()
    db.refresh(topic)
    return topic


@router.get("/topics/{topic_id}", response_model=TopicRead)
def get_topic(topic_id: str, db: Session = Depends(get_db)) -> Topic:
    topic = db.get(Topic, topic_id)
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    return topic
