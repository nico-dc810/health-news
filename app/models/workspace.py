from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base
from app.models.base import UUIDTimestampMixin


class Workspace(UUIDTimestampMixin, Base):
    __tablename__ = "workspaces"

    owner_id: Mapped[str] = mapped_column(index=True)
    name: Mapped[str] = mapped_column(String(255))
    plan: Mapped[str] = mapped_column(String(50), default="free")
    status: Mapped[str] = mapped_column(String(50), default="active")

