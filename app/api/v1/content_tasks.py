from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.compliance_review import ComplianceReview
from app.models.content_task import ContentTask
from app.models.organization import Organization
from app.models.topic import Topic
from app.schemas.content_task import ContentGenerateRequest, ContentTaskRead
from app.services.agent_logger import log_agent_run
from app.services.compliance import review_content
from app.services.content_generator import generate_content
from app.services.llm_gateway import chat_completion, resolve_model_config

router = APIRouter()


@router.get("/organizations/{organization_id}/content-tasks", response_model=list[ContentTaskRead])
def list_content_tasks(organization_id: str, db: Session = Depends(get_db)) -> list[ContentTask]:
    statement = (
        select(ContentTask)
        .where(ContentTask.organization_id == organization_id)
        .order_by(ContentTask.created_at.desc())
    )
    return list(db.scalars(statement))


@router.post("/content-tasks/generate", response_model=ContentTaskRead)
def generate_content_task(
    payload: ContentGenerateRequest,
    db: Session = Depends(get_db),
) -> ContentTask:
    organization = db.get(Organization, payload.organization_id)
    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found")
    topic = db.get(Topic, payload.topic_id) if payload.topic_id else None

    generated = generate_content(
        organization,
        topic,
        topic_title=payload.topic_title,
        content_type=payload.content_type,
        platform=payload.platform,
    )
    model_config = resolve_model_config(
        db,
        workspace_id=organization.workspace_id,
        organization_id=payload.organization_id,
        use_case="content_producer",
    )
    if model_config and model_config.provider != "mock":
        topic_title = topic.title if topic else payload.topic_title or "健康内容选题"
        generated["body"] = chat_completion(
            model_config,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "你是大健康机构内容运营专家。请生成合规、克制、有真人温度的内容，"
                        "避免疗效承诺、绝对化表达、疾病治疗暗示和夸大宣传。"
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"机构：{organization.name}\n"
                        f"目标客户：{organization.target_audience or '未填写'}\n"
                        f"核心服务：{organization.core_services or '未填写'}\n"
                        f"平台：{payload.platform}\n"
                        f"内容类型：{payload.content_type}\n"
                        f"选题：{topic_title}\n"
                        "请直接输出正文。"
                    ),
                },
            ],
        )
    compliance = review_content(generated["body"])
    task = ContentTask(
        organization_id=payload.organization_id,
        ip_profile_id=payload.ip_profile_id,
        topic_id=payload.topic_id,
        content_type=payload.content_type,
        platform=payload.platform,
        title=generated["title"],
        body=generated["body"],
        cover_text=generated["cover_text"],
        source_material_ids=generated["used_materials"],
        status="draft",
        compliance_status="approved" if compliance["risk_level"] == "low" else "review_required",
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    db.add(
        ComplianceReview(
            content_task_id=task.id,
            organization_id=payload.organization_id,
            input_text=generated["body"],
            risk_level=compliance["risk_level"],
            risk_items=compliance["risk_items"],
            suggestions=compliance["suggestions"],
            rewritten_content=compliance["rewritten_content"],
        )
    )
    db.commit()

    log_agent_run(
        db,
        agent_name="content_producer",
        workspace_id=organization.workspace_id,
        organization_id=payload.organization_id,
        input_payload=payload.model_dump(),
        output_payload={"content": generated, "compliance": compliance},
    )
    return task


@router.get("/content-tasks/{content_task_id}", response_model=ContentTaskRead)
def get_content_task(content_task_id: str, db: Session = Depends(get_db)) -> ContentTask:
    task = db.get(ContentTask, content_task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Content task not found")
    return task
