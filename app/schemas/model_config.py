from pydantic import BaseModel, Field

from app.schemas.common import TimestampedModel


class ModelConfigCreate(BaseModel):
    workspace_id: str
    organization_id: str | None = None
    name: str
    provider: str = "mock"
    api_base_url: str | None = None
    api_key: str | None = None
    model_name: str = "mock-model"
    use_case: str = "default"
    temperature: float = Field(default=0.7, ge=0, le=2)
    max_tokens: int = Field(default=1200, ge=1, le=32000)
    is_default: bool = False


class ModelConfigUpdate(BaseModel):
    name: str | None = None
    provider: str | None = None
    api_base_url: str | None = None
    api_key: str | None = None
    model_name: str | None = None
    use_case: str | None = None
    temperature: float | None = Field(default=None, ge=0, le=2)
    max_tokens: int | None = Field(default=None, ge=1, le=32000)
    is_default: bool | None = None
    status: str | None = None


class ModelConfigRead(TimestampedModel):
    workspace_id: str
    organization_id: str | None = None
    name: str
    provider: str
    api_base_url: str | None = None
    masked_api_key: str | None = None
    model_name: str
    use_case: str
    temperature: float
    max_tokens: int
    is_default: bool
    status: str


class ModelConfigTestResponse(BaseModel):
    ok: bool
    provider: str
    model_name: str
    message: str
    sample: str | None = None

