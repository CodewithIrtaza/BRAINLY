"""
Brainly API - Workspace Schemas

Pydantic models for workspace and agent configuration.
"""
from datetime import datetime
from typing import Any
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class WorkspaceBase(BaseModel):
    """Base workspace fields."""
    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=100, pattern=r"^[a-z0-9-]+$")


class WorkspaceCreate(WorkspaceBase):
    """Workspace creation request."""
    pass


class WorkspaceUpdate(BaseModel):
    """Workspace update request."""
    name: str | None = Field(None, min_length=1, max_length=255)
    settings: dict[str, Any] | None = None


class WorkspaceResponse(WorkspaceBase):
    """Workspace response."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    owner_id: UUID
    plan: str
    settings: dict[str, Any]
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None


class AgentConfigBase(BaseModel):
    """Base agent configuration fields."""
    name: str = Field(default="Brainly Assistant", min_length=1, max_length=255)
    description: str | None = None
    instructions: str | None = None
    welcome_message: str = Field(
        default="Hello! How can I help you?", min_length=1, max_length=500
    )
    model: str = Field(default="nvidia/llama-3.1-70b", min_length=1, max_length=100)
    temperature: float = Field(default=0.3, ge=0.0, le=2.0)
    max_tokens: int = Field(default=2048, ge=1, le=8192)
    fallback_msg: str = Field(
        default="I don't have that information. Would you like to talk to a human?",
        min_length=1,
        max_length=500,
    )


class AgentConfigUpdate(AgentConfigBase):
    """Agent configuration update request."""
    pass


class AgentConfigResponse(AgentConfigBase):
    """Agent configuration response."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workspace_id: UUID
    created_at: datetime
    updated_at: datetime