from datetime import datetime

from sqlalchemy import DateTime, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base
from app.models.base import UUIDTimestampMixin


class KnowledgeSource(UUIDTimestampMixin, Base):
    __tablename__ = "knowledge_sources"

    workspace_id: Mapped[str] = mapped_column(index=True)
    organization_id: Mapped[str | None] = mapped_column(index=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    source_type: Mapped[str] = mapped_column(String(100), default="website")
    url: Mapped[str] = mapped_column(Text)
    crawl_frequency: Mapped[str] = mapped_column(String(50), default="daily")
    category: Mapped[str | None] = mapped_column(String(100), index=True)
    credibility_level: Mapped[str] = mapped_column(String(50), default="medium")
    status: Mapped[str] = mapped_column(String(50), default="active")
    last_crawled_at: Mapped[datetime | None] = mapped_column(DateTime)


class KnowledgeItem(UUIDTimestampMixin, Base):
    __tablename__ = "knowledge_items"

    source_id: Mapped[str] = mapped_column(index=True)
    organization_id: Mapped[str | None] = mapped_column(index=True)
    title: Mapped[str] = mapped_column(String(500), index=True)
    url: Mapped[str] = mapped_column(Text, index=True)
    author: Mapped[str | None] = mapped_column(String(255))
    published_at: Mapped[datetime | None] = mapped_column(DateTime)
    crawled_at: Mapped[datetime] = mapped_column(DateTime)
    raw_text: Mapped[str | None] = mapped_column(Text)
    summary: Mapped[str | None] = mapped_column(Text)
    category: Mapped[str | None] = mapped_column(String(100), index=True)
    tags: Mapped[list | None] = mapped_column(JSON)
    audiences: Mapped[list | None] = mapped_column(JSON)
    pain_points: Mapped[list | None] = mapped_column(JSON)
    topic_suggestions: Mapped[list | None] = mapped_column(JSON)
    compliance_risk: Mapped[dict | None] = mapped_column(JSON)
    credibility_score: Mapped[int] = mapped_column(default=50)
    status: Mapped[str] = mapped_column(String(50), default="pending_review")

