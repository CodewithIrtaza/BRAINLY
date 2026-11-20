"""
Brainly API - Knowledge Base Schemas

Pydantic models for KB source management.
"""
from datetime import datetime
from typing import Any
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class KBSourceBase(BaseModel):
    """Base KB source fields."""
    type: str = Field(..., pattern=r"^(pdf|txt|faq|url)$")
    filename: str | None = Field(None, max_length=255)
    url: str | None = None
    meta: dict[str, Any] = Field(default_factory=dict)


class KBSourceCreate(KBSourceBase):
    """KB source creation request."""
    pass


class KBSourceUpdate(BaseModel):
    """KB source update request."""
    filename: str | None = Field(None, max_length=255)
    url: str | None = None
    meta: dict[str, Any] | None = None


class KBSourceResponse(KBSourceBase):
    """KB source response."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workspace_id: UUID
    status: str
    error_message: str | None
    chunk_count: int
    token_count: int
    file_size: int | None
    storage_path: str | None
    created_at: datetime
    updated_at: datetime
    processed_at: datetime | None


class FAQEntryCreate(BaseModel):
    """Single FAQ entry."""
    question: str = Field(..., min_length=1, max_length=1000)
    answer: str = Field(..., min_length=1, max_length=5000)


class FAQBulkCreate(BaseModel):
    """Bulk FAQ creation request."""
    entries: list[FAQEntryCreate] = Field(..., min_length=1, max_length=100)