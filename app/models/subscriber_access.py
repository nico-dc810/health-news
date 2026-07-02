from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base
from app.models.base import UUIDTimestampMixin


class SubscriberAccess(UUIDTimestampMixin, Base):
    __tablename__ = "subscriber_accesses"

    phone: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    payment_status: Mapped[str] = mapped_column(String(50), default="pending_payment")
    status: Mapped[str] = mapped_column(String(50), default="active")
    activated_at: Mapped[datetime | None] = mapped_column(DateTime)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime)
    remark: Mapped[str | None] = mapped_column(String(500), nullable=True)
