from pydantic import BaseModel

from app.schemas.common import TimestampedModel


class MaterialCreate(BaseModel):
    workspace_id: str
    organization_id: str
    title: str
    material_type: str
    source_type: str = "manual"
    raw_text: str | None = None


class MaterialRead(TimestampedModel):
    workspace_id: str
    organization_id: str
    title: str
    material_type: str
    source_type: str
    raw_text: str | None = None
    summary: str | None = None
    structured_data: dict | None = None
    tags: list | None = None
    risk_level: str | None = None
    status: str


class MaterialAnalyzeResponse(BaseModel):
    material: MaterialRead
    analysis: dict

