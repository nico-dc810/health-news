from datetime import datetime

from sqlalchemy import DateTime, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base
from app.models.base import UUIDTimestampMixin


class ContentTask(UUIDTimestampMixin, Base):
    __tablename__ = "content_tasks"

    organization_id: Mapped[str] = mapped_column(index=True)
    ip_profile_id: Mapped[str | None] = mapped_column(index=True)
    topic_id: Mapped[str | None] = mapped_column(index=True)
    content_type: Mapped[str] = mapped_column(String(100), index=True)
    platform: Mapped[str | None] = mapped_column(String(100), index=True)
    title: Mapped[str | None] = mapped_column(String(255))
    body: Mapped[str | None] = mapped_column(Text)
    cover_text: Mapped[str | None] = mapped_column(String(255))
    source_material_ids: Mapped[list | None] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(50), default="draft")
    compliance_status: Mapped[str] = mapped_column(String(50), default="pending")
    publish_time: Mapped[datetime | None] = mapped_column(DateTime)

