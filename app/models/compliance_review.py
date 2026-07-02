from sqlalchemy import JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base
from app.models.base import UUIDTimestampMixin


class ComplianceReview(UUIDTimestampMixin, Base):
    __tablename__ = "compliance_reviews"

    content_task_id: Mapped[str | None] = mapped_column(index=True)
    organization_id: Mapped[str] = mapped_column(index=True)
    input_text: Mapped[str] = mapped_column(Text)
    risk_level: Mapped[str | None] = mapped_column(String(50))
    risk_items: Mapped[list | None] = mapped_column(JSON)
    suggestions: Mapped[list | None] = mapped_column(JSON)
    rewritten_content: Mapped[str | None] = mapped_column(Text)
    review_status: Mapped[str] = mapped_column(String(50), default="completed")

