from sqlalchemy import JSON, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base
from app.models.base import UUIDTimestampMixin


class AgentRun(UUIDTimestampMixin, Base):
    __tablename__ = "agent_runs"

    agent_name: Mapped[str] = mapped_column(String(100), index=True)
    workspace_id: Mapped[str | None] = mapped_column(index=True)
    organization_id: Mapped[str | None] = mapped_column(index=True)
    user_id: Mapped[str | None] = mapped_column(index=True)
    input: Mapped[dict | None] = mapped_column(JSON)
    retrieved_materials: Mapped[list | None] = mapped_column(JSON)
    output: Mapped[dict | None] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(50), default="success")
    token_usage: Mapped[dict | None] = mapped_column(JSON)
    cost: Mapped[float | None] = mapped_column(Numeric(12, 6))
    error_message: Mapped[str | None] = mapped_column(Text)

