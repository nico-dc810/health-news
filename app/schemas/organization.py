from pydantic import BaseModel

from app.schemas.common import TimestampedModel


class OrganizationCreate(BaseModel):
    workspace_id: str
    name: str
    industry_type: str | None = None
    city: str | None = None
    description: str | None = None
    target_audience: str | None = None
    core_services: str | None = None
    compliance_notes: str | None = None
    forbidden_words: str | None = None


class OrganizationUpdate(BaseModel):
    name: str | None = None
    industry_type: str | None = None
    city: str | None = None
    description: str | None = None
    target_audience: str | None = None
    core_services: str | None = None
    compliance_notes: str | None = None
    forbidden_words: str | None = None


class OrganizationRead(TimestampedModel):
    workspace_id: str
    name: str
    industry_type: str | None = None
    city: str | None = None
    description: str | None = None
    target_audience: str | None = None
    core_services: str | None = None
    compliance_notes: str | None = None
    forbidden_words: str | None = None

