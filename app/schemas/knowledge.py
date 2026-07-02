from datetime import datetime

from pydantic import BaseModel

from app.schemas.common import TimestampedModel


class KnowledgeSourceCreate(BaseModel):
    workspace_id: str
    organization_id: str | None = None
    name: str
    source_type: str = "website"
    url: str
    crawl_frequency: str = "daily"
    category: str | None = None
    credibility_level: str = "medium"


class KnowledgeSourceRead(TimestampedModel):
    workspace_id: str
    organization_id: str | None = None
    name: str
    source_type: str
    url: str
    crawl_frequency: str
    category: str | None = None
    credibility_level: str
    status: str
    last_crawled_at: datetime | None = None


class KnowledgeItemRead(TimestampedModel):
    source_id: str
    organization_id: str | None = None
    title: str
    url: str
    author: str | None = None
    published_at: datetime | None = None
    crawled_at: datetime
    raw_text: str | None = None
    summary: str | None = None
    category: str | None = None
    tags: list | None = None
    audiences: list | None = None
    pain_points: list | None = None
    topic_suggestions: list | None = None
    compliance_risk: dict | None = None
    credibility_score: int
    status: str


class KnowledgeCrawlResponse(BaseModel):
    source: KnowledgeSourceRead
    items: list[KnowledgeItemRead]
    message: str


class KnowledgeSourceSeedRequest(BaseModel):
    workspace_id: str = "demo-workspace"
    organization_id: str | None = None
    reset_existing: bool = False


class RepositoryOptionRead(BaseModel):
    id: str
    name: str
    role: str
    suitable_for: list[str]
    limitations: list[str]
    recommended_use: str
    status: str


class IntelligenceDashboardRead(BaseModel):
    source_count: int
    active_source_count: int
    item_count: int
    high_risk_count: int
    latest_items: list[KnowledgeItemRead]
    category_counts: dict[str, int]
    repository_options: list[RepositoryOptionRead]


class IntelligenceCrawlRequest(BaseModel):
    workspace_id: str = "demo-workspace"
    organization_id: str | None = None
    max_sources: int = 3


class IntelligenceCrawlResponse(BaseModel):
    source_count: int
    item_count: int
    errors: list[str]
    message: str
