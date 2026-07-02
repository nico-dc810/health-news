from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.compliance_review import ComplianceReview
from app.models.organization import Organization
from app.schemas.compliance import ComplianceReviewRead, ComplianceReviewRequest
from app.services.llm_agents import review_compliance_with_llm
from app.services.llm_gateway import resolve_model_config
from app.services.compliance import review_content

router = APIRouter()


@router.post("/review", response_model=ComplianceReviewRead)
def create_compliance_review(
    payload: ComplianceReviewRequest,
    db: Session = Depends(get_db),
) -> ComplianceReview:
    organization = db.get(Organization, payload.organization_id)
    model_config = resolve_model_config(
        db,
        workspace_id=organization.workspace_id if organization else None,
        organization_id=payload.organization_id,
        use_case="compliance",
    )
    if model_config and model_config.provider != "mock":
        try:
            result = review_compliance_with_llm(model_config, text=payload.input_text)
        except ValueError:
            result = review_content(payload.input_text)
    else:
        result = review_content(payload.input_text)
    review = ComplianceReview(
        content_task_id=payload.content_task_id,
        organization_id=payload.organization_id,
        input_text=payload.input_text,
        risk_level=result["risk_level"],
        risk_items=result["risk_items"],
        suggestions=result["suggestions"],
        rewritten_content=result["rewritten_content"],
        review_status="completed",
    )
    db.add(review)
    db.commit()
    db.refresh(review)
    return review
