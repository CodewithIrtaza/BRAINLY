"""
Brainly API - Lead Schemas

Pydantic models for lead management.
"""
from datetime import datetime
from typing import Any
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class LeadResponse(BaseModel):
    """Lead response."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workspace_id: UUID
    conversation_id: UUID | None
    data: dict[str, Any]
    consent: bool
    source: str
    status: str
    notes: str | None
    created_at: datetime
    updated_at: datetime


class LeadUpdate(BaseModel):
    """Lead update request."""
    status: str | None = Field(None, pattern=r"^(new|contacted|qualified|lost)$")
    notes: str | None = Field(None, max_length=1000)