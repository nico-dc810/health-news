from pydantic import BaseModel

from app.schemas.common import TimestampedModel


class ContentGenerateRequest(BaseModel):
    organization_id: str
    ip_profile_id: str | None = None
    topic_id: str | None = None
    topic_title: str | None = None
    content_type: str
    platform: str = "小红书"


class ContentTaskRead(TimestampedModel):
    organization_id: str
    ip_profile_id: str | None = None
    topic_id: str | None = None
    content_type: str
    platform: str | None = None
    title: str | None = None
    body: str | None = None
    cover_text: str | None = None
    source_material_ids: list | None = None
    status: str
    compliance_status: str

