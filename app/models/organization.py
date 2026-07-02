from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base
from app.models.base import UUIDTimestampMixin


class Organization(UUIDTimestampMixin, Base):
    __tablename__ = "organizations"

    workspace_id: Mapped[str] = mapped_column(index=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    industry_type: Mapped[str | None] = mapped_column(String(100))
    city: Mapped[str | None] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(Text)
    target_audience: Mapped[str | None] = mapped_column(Text)
    core_services: Mapped[str | None] = mapped_column(Text)
    compliance_notes: Mapped[str | None] = mapped_column(Text)
    forbidden_words: Mapped[str | None] = mapped_column(Text)

