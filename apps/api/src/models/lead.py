"""
Brainly API - Lead Model

Lead capture and management.
"""
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from .workspace import Workspace
    from .conversation import Conversation


class Lead(Base, UUIDMixin, TimestampMixin):
    """Captured lead from chat widget."""

    __tablename__ = "leads"

    workspace_id: Mapped[UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    conversation_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("conversations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    data: Mapped[dict] = mapped_column(JSONB, nullable=False)  # {name, phone, email, custom...}
    consent: Mapped[bool] = mapped_column(default=True, nullable=False)  # GDPR consent
    source: Mapped[str] = mapped_column(String(50), default="widget", nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), default="new", nullable=False, index=True
    )  # new, contacted, qualified, lost
    notes: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    # Relationships
    workspace: Mapped["Workspace"] = relationship("Workspace", back_populates="leads")
    conversation: Mapped["Conversation | None"] = relationship(
        "Conversation", back_populates="leads"
    )

    __table_args__ = (
        Index("idx_leads_workspace_status", "workspace_id", "status"),
        Index("idx_leads_workspace_created", "workspace_id", "created_at"),
    )