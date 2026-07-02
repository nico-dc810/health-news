from pydantic import BaseModel

from app.schemas.common import TimestampedModel


class ComplianceReviewRequest(BaseModel):
    organization_id: str
    content_task_id: str | None = None
    input_text: str


class ComplianceReviewRead(TimestampedModel):
    content_task_id: str | None = None
    organization_id: str
    input_text: str
    risk_level: str | None = None
    risk_items: list | None = None
    suggestions: list | None = None
    rewritten_content: str | None = None
    review_status: str

