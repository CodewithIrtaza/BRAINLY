"""
Brainly API - Knowledge Base Models

KBSource and KBChunk models for document storage and vector search.
"""
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector

from .base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from .workspace import Workspace
    from .conversation import Message


class KBSource(Base, UUIDMixin, TimestampMixin):
    """Knowledge base source document."""

    __tablename__ = "kb_sources"

    workspace_id: Mapped[UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    type: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # pdf, txt, faq, url
    filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    url: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), default="pending", nullable=False, index=True
    )  # pending, processing, ready, failed
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    chunk_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    token_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    file_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    storage_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    meta: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    workspace: Mapped["Workspace"] = relationship("Workspace", back_populates="kb_sources")
    chunks: Mapped[list["KBChunk"]] = relationship(
        "KBChunk",
        back_populates="source",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    __table_args__ = (
        Index("idx_kb_sources_workspace_status", "workspace_id", "status"),
    )


class KBChunk(Base, UUIDMixin, TimestampMixin):
    """Knowledge base chunk with vector embedding."""

    __tablename__ = "kb_chunks"

    source_id: Mapped[UUID] = mapped_column(
        ForeignKey("kb_sources.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    workspace_id: Mapped[UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    embedding: Mapped[list[float]] = mapped_column(Vector(1024), nullable=True)
    metadata: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    token_count: Mapped[int] = mapped_column(Integer, nullable=False)

    # Relationships
    source: Mapped["KBSource"] = relationship("KBSource", back_populates="chunks")
    workspace: Mapped["Workspace"] = relationship("Workspace", lazy="selectin")

    __table_args__ = (
        Index("idx_kb_chunks_workspace_source", "workspace_id", "source_id"),
        # IVFFlat index for vector similarity search
        Index(
            "idx_kb_chunks_embedding",
            "embedding",
            postgresql_using="ivfflat",
            postgresql_with={"lists": 100},
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )