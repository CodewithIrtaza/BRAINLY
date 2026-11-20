"""
Brainly API - Conversation Models

Conversation and Message models for chat sessions.
"""
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from .workspace import Workspace


class Conversation(Base, UUIDMixin, TimestampMixin):
    """Conversation session."""

    __tablename__ = "conversations"

    workspace_id: Mapped[UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    session_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    visitor_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    language: Mapped[str] = mapped_column(
        String(20), default="en", nullable=False
    )  # en, ur, ur-Roman
    status: Mapped[str] = mapped_column(
        String(20), default="active", nullable=False, index=True
    )  # active, escalated, closed, archived
    has_lead: Mapped[bool] = mapped_column(default=False, nullable=False)
    message_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    metadata: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=None, nullable=False
    )
    last_message_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=None, nullable=False
    )
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    workspace: Mapped["Workspace"] = relationship("Workspace", back_populates="conversations")
    messages: Mapped[list["Message"]] = relationship(
        "Message",
        back_populates="conversation",
        cascade="all, delete-orphan",
        lazy="dynamic",
        order_by="Message.created_at",
    )

    __table_args__ = (
        Index("idx_conversations_workspace_status", "workspace_id", "status"),
        Index("idx_conversations_workspace_last_msg", "workspace_id", "last_message_at"),
    )


class Message(Base, UUIDMixin, TimestampMixin):
    """Individual chat message."""

    __tablename__ = "messages"

    conversation_id: Mapped[UUID] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # user, assistant, system
    content: Mapped[str] = mapped_column(Text, nullable=False)
    language: Mapped[str] = mapped_column(String(20), default="en", nullable=False)
    citations: Mapped[list[dict]] = mapped_column(JSONB, default=list, nullable=False)
    token_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    model_used: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_fallback: Mapped[bool] = mapped_column(default=False, nullable=False, index=True)
    meta: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    # Relationships
    conversation: Mapped["Conversation"] = relationship(
        "Conversation", back_populates="messages"
    )

    __table_args__ = (
        Index("idx_messages_conversation_created", "conversation_id", "created_at"),
        Index("idx_messages_fallback", "is_fallback", postgresql_where="is_fallback = true"),
    )