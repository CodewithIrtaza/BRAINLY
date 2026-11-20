"""
Brainly API - Chat Schemas

Pydantic models for chat messages, conversations, and streaming.
"""
from datetime import datetime
from typing import Any, Literal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class ChatMessageRequest(BaseModel):
    """Chat message request from widget."""
    workspace_slug: str = Field(..., min_length=1, max_length=100)
    message: str = Field(..., min_length=1, max_length=4000)
    session_id: str | None = Field(None, max_length=100)
    language: Literal["auto", "en", "ur", "ur-Roman"] = "auto"


class Citation(BaseModel):
    """Source citation in response."""
    chunk_id: UUID
    preview: str = Field(..., max_length=200)
    score: float = Field(..., ge=0.0, le=1.0)


class ChatMessageStreamChunk(BaseModel):
    """Single chunk in streaming response."""
    type: Literal["token", "citation", "done", "error"]
    delta: str | None = None
    citations: list[Citation] | None = None
    message_id: UUID | None = None
    conversation_id: UUID | None = None
    fallback: bool | None = None
    error: str | None = None


class ChatMessageResponse(BaseModel):
    """Complete chat message response (non-streaming)."""
    message_id: UUID
    conversation_id: UUID
    content: str
    citations: list[Citation]
    fallback: bool
    language: str


class ConversationResponse(BaseModel):
    """Conversation with messages."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workspace_id: UUID
    session_id: str
    visitor_id: str | None
    language: str
    status: str
    has_lead: bool
    message_count: int
    metadata: dict[str, Any]
    started_at: datetime
    last_message_at: datetime
    closed_at: datetime | None
    messages: list["MessageResponse"] = []


class MessageResponse(BaseModel):
    """Message response."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    conversation_id: UUID
    role: str
    content: str
    language: str
    citations: list[Citation]
    token_count: int | None
    model_used: str | None
    is_fallback: bool
    meta: dict[str, Any]
    created_at: datetime


class ConversationListResponse(BaseModel):
    """Paginated conversation list."""
    data: list[ConversationResponse]
    meta: dict[str, Any]


class EscalationRequest(BaseModel):
    """Human escalation request."""
    conversation_id: UUID
    reason: str = Field(default="User requested human assistance", max_length=500)


class LeadCaptureRequest(BaseModel):
    """Lead capture form submission."""
    conversation_id: UUID
    data: dict[str, Any] = Field(..., description="Lead form data: name, phone, email, custom fields")
    consent: bool = Field(..., description="GDPR consent")