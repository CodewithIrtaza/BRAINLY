"""
Brainly API - FAQ Suggestion Schemas

Pydantic models for FAQ suggestion management.
"""
from datetime import datetime
from typing import Any
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class FAQSuggestionResponse(BaseModel):
    """FAQ suggestion response."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workspace_id: UUID
    question: str
    answer: str
    source_conversation_ids: list[UUID]
    confidence: float
    status: str
    reviewed_by: UUID | None
    reviewed_at: datetime | None
    created_at: datetime


class FAQSuggestionAction(BaseModel):
    """FAQ suggestion action request."""
    action: str = Field(..., pattern=r"^(approve|reject)$")