from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base
from app.models.base import UUIDTimestampMixin


class IpProfile(UUIDTimestampMixin, Base):
    __tablename__ = "ip_profiles"

    organization_id: Mapped[str] = mapped_column(index=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    role_identity: Mapped[str | None] = mapped_column(String(255))
    expertise: Mapped[str | None] = mapped_column(Text)
    target_audience: Mapped[str | None] = mapped_column(Text)
    content_positioning: Mapped[str | None] = mapped_column(Text)
    tone_style: Mapped[str | None] = mapped_column(String(100))
    style_rules: Mapped[str | None] = mapped_column(Text)
    forbidden_words: Mapped[str | None] = mapped_column(Text)
    compliance_boundary: Mapped[str | None] = mapped_column(Text)

