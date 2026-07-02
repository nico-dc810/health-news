from pydantic import BaseModel

from app.schemas.common import TimestampedModel


class TopicGenerateRequest(BaseModel):
    organization_id: str
    ip_profile_id: str | None = None
    platform: str = "小红书"
    conversion_goal: str = "引导咨询"
    count: int = 5


class TopicCreate(BaseModel):
    organization_id: str
    ip_profile_id: str | None = None
    title: str
    topic_type: str | None = None
    target_audience: str | None = None
    pain_point: str | None = None
    platform: str | None = None
    conversion_goal: str | None = None
    risk_level: str | None = None
    priority: int = 0
    source_material_ids: list | None = None


class TopicRead(TimestampedModel):
    organization_id: str
    ip_profile_id: str | None = None
    title: str
    topic_type: str | None = None
    target_audience: str | None = None
    pain_point: str | None = None
    platform: str | None = None
    conversion_goal: str | None = None
    risk_level: str | None = None
    priority: int
    source_material_ids: list | None = None
    status: str

