from sqlalchemy import JSON, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base
from app.models.base import UUIDTimestampMixin


class Topic(UUIDTimestampMixin, Base):
    __tablename__ = "topics"

    organization_id: Mapped[str] = mapped_column(index=True)
    ip_profile_id: Mapped[str | None] = mapped_column(index=True)
    title: Mapped[str] = mapped_column(String(255), index=True)
    topic_type: Mapped[str | None] = mapped_column(String(100))
    target_audience: Mapped[str | None] = mapped_column(Text)
    pain_point: Mapped[str | None] = mapped_column(Text)
    platform: Mapped[str | None] = mapped_column(String(100))
    conversion_goal: Mapped[str | None] = mapped_column(String(100))
    risk_level: Mapped[str | None] = mapped_column(String(50))
    priority: Mapped[int] = mapped_column(Integer, default=0)
    source_material_ids: Mapped[list | None] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(50), default="active")

