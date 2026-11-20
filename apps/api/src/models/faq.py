"""
Brainly API - FAQ Suggestion Model

Auto-generated FAQ candidates from conversations.
"""
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ARRAY, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from .workspace import Workspace


class FAQSuggestion(Base, UUIDMixin, TimestampMixin):
    """Auto-generated FAQ suggestion from conversation analysis."""

    __tablename__ = "faq_suggestions"

    workspace_id: Mapped[UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    source_conversation_ids: Mapped[list[UUID]] = mapped_column(
        ARRAY(PG_UUID(as_uuid=True)), nullable=False
    )
    confidence: Mapped[float] = mapped_column(nullable=False)  # 0.0 - 1.0
    status: Mapped[str] = mapped_column(
        String(20), default="pending", nullable=False, index=True
    )  # pending, approved, rejected, added
    reviewed_by: Mapped[UUID | None] = mapped_column(
        ForeignKey("auth.users.id", ondelete="SET NULL"), nullable=True
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    workspace: Mapped["Workspace"] = relationship("Workspace", back_populates="faq_suggestions")

    __table_args__ = (
        Index("idx_faq_suggestions_workspace_status", "workspace_id", "status"),
        Index("idx_faq_suggestions_workspace_created", "workspace_id", "created_at"),
    )