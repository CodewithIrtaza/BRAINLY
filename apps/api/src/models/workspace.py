"""
Brainly API - Workspace Models

Workspace, Agent, and WorkspaceMember models.
"""
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from .kb import KBSource
    from .conversation import Conversation
    from .lead import Lead
    from .faq import FAQSuggestion


class Workspace(Base, UUIDMixin, TimestampMixin):
    """Workspace - core tenant entity."""

    __tablename__ = "workspaces"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    owner_id: Mapped[UUID] = mapped_column(
        ForeignKey("auth.users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    plan: Mapped[str] = mapped_column(String(50), default="free", nullable=False)
    settings: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    agent: Mapped["Agent"] = relationship(
        "Agent",
        back_populates="workspace",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    kb_sources: Mapped[list["KBSource"]] = relationship(
        "KBSource",
        back_populates="workspace",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )
    conversations: Mapped[list["Conversation"]] = relationship(
        "Conversation",
        back_populates="workspace",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )
    leads: Mapped[list["Lead"]] = relationship(
        "Lead",
        back_populates="workspace",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )
    faq_suggestions: Mapped[list["FAQSuggestion"]] = relationship(
        "FAQSuggestion",
        back_populates="workspace",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )
    members: Mapped[list["WorkspaceMember"]] = relationship(
        "WorkspaceMember",
        back_populates="workspace",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )


class Agent(Base, UUIDMixin, TimestampMixin):
    """Agent configuration - one per workspace in V1."""

    __tablename__ = "agents"

    workspace_id: Mapped[UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), default="Brainly Assistant", nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    instructions: Mapped[str | None] = mapped_column(Text, nullable=True)
    welcome_message: Mapped[str] = mapped_column(
        Text, default="Hello! How can I help you?", nullable=False
    )
    model: Mapped[str] = mapped_column(String(100), default="nvidia/llama-3.1-70b", nullable=False)
    temperature: Mapped[float] = mapped_column(default=0.3, nullable=False)
    max_tokens: Mapped[int] = mapped_column(default=2048, nullable=False)
    fallback_msg: Mapped[str] = mapped_column(
        Text,
        default="I don't have that information. Would you like to talk to a human?",
        nullable=False,
    )

    # Relationships
    workspace: Mapped["Workspace"] = relationship("Workspace", back_populates="agent")


class WorkspaceMember(Base, UUIDMixin, TimestampMixin):
    """Workspace membership for team collaboration."""

    __tablename__ = "workspace_members"

    workspace_id: Mapped[UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("auth.users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[str] = mapped_column(String(50), default="member", nullable=False)

    # Relationships
    workspace: Mapped["Workspace"] = relationship("Workspace", back_populates="members")

    __table_args__ = (
        UniqueConstraint("workspace_id", "user_id", name="uq_workspace_member"),
    )