from sqlalchemy import JSON, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base
from app.models.base import UUIDTimestampMixin


class Material(UUIDTimestampMixin, Base):
    __tablename__ = "materials"

    workspace_id: Mapped[str] = mapped_column(index=True)
    organization_id: Mapped[str] = mapped_column(index=True)
    title: Mapped[str] = mapped_column(String(255), index=True)
    material_type: Mapped[str] = mapped_column(String(100), index=True)
    source_type: Mapped[str] = mapped_column(String(100), default="manual")
    raw_text: Mapped[str | None] = mapped_column(Text)
    summary: Mapped[str | None] = mapped_column(Text)
    structured_data: Mapped[dict | None] = mapped_column(JSON)
    tags: Mapped[list | None] = mapped_column(JSON)
    risk_level: Mapped[str | None] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(50), default="active")


class MaterialChunk(UUIDTimestampMixin, Base):
    __tablename__ = "material_chunks"

    material_id: Mapped[str] = mapped_column(index=True)
    chunk_index: Mapped[int] = mapped_column(Integer)
    chunk_text: Mapped[str] = mapped_column(Text)
    summary: Mapped[str | None] = mapped_column(Text)
    embedding: Mapped[list | None] = mapped_column(JSON)
    chunk_metadata: Mapped[dict | None] = mapped_column(JSON)

