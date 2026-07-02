from sqlalchemy import Boolean, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base
from app.models.base import UUIDTimestampMixin


class ModelConfig(UUIDTimestampMixin, Base):
    __tablename__ = "model_configs"

    workspace_id: Mapped[str] = mapped_column(index=True)
    organization_id: Mapped[str | None] = mapped_column(index=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    provider: Mapped[str] = mapped_column(String(100), default="mock")
    api_base_url: Mapped[str | None] = mapped_column(Text)
    api_key: Mapped[str | None] = mapped_column(Text)
    model_name: Mapped[str] = mapped_column(String(255), default="mock-model")
    use_case: Mapped[str] = mapped_column(String(100), default="default")
    temperature: Mapped[float] = mapped_column(Float, default=0.7)
    max_tokens: Mapped[int] = mapped_column(Integer, default=1200)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str] = mapped_column(String(50), default="active")

