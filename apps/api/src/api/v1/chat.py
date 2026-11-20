"""
Brainly API - Chat Routes

Chat message, conversation, escalation, and lead capture endpoints.
"""
from typing import Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ....config import get_settings
from ....database import get_db
from ....models import Workspace, Conversation, Message
from ....schemas.chat import (
    ChatMessageRequest,
    ChatMessageResponse,
    ConversationResponse,
    ConversationListResponse,
    EscalationRequest,
    LeadCaptureRequest,
)
from ....api.deps import get_workspace_from_slug, get_authenticated_workspace

router = APIRouter()


# Public Widget Endpoints (no auth required, uses workspace slug)
@router.post("/message")
async def send_message(
    request: ChatMessageRequest,
    workspace: Workspace = Depends(get_workspace_from_slug),
    db: AsyncSession = Depends(get_db),
):
    """
    Send a chat message and get streaming response.

    This is the main widget endpoint - public access via workspace slug.
    """
    settings = get_settings()

    if settings.ENVIRONMENT == "development":
        # Return mock streaming response
        from uuid import uuid4
        import json

        async def mock_stream():
            chunks = [
                {"type": "token", "delta": "Hello! "},
                {"type": "token", "delta": "I'm "},
                {"type": "token", "delta": "Brainly "},
                {"type": "token", "delta": "Assistant. "},
                {"type": "token", "delta": "How "},
                {"type": "token", "delta": "can "},
                {"type": "token", "delta": "I "},
                {"type": "token", "delta": "help "},
                {"type": "token", "delta": "you "},
                {"type": "token", "delta": "today?"},
                {
                    "type": "done",
                    "message_id": str(uuid4()),
                    "conversation_id": str(uuid4()),
                    "fallback": False,
                },
            ]
            for chunk in chunks:
                yield f"data: {json.dumps(chunk)}\n\n"

        return StreamingResponse(
            mock_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            },
        )

    # TODO: Implement actual RAG pipeline
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="RAG chat pipeline not implemented yet",
    )


@router.post("/escalate")
async def escalate_to_human(
    request: EscalationRequest,
    workspace: Workspace = Depends(get_workspace_from_slug),
    db: AsyncSession = Depends(get_db),
):
    """Request human agent escalation."""
    from sqlalchemy import select

    result = await db.execute(
        select(Conversation).where(
            Conversation.id == request.conversation_id,
            Conversation.workspace_id == workspace.id,
        )
    )
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    conversation.status = "escalated"
    await db.commit()

    # TODO: Send notification email/Slack
    return {"data": {"success": True, "message": "Team notified. Expected response: 15 minutes"}}


@router.post("/lead")
async def capture_lead(
    request: LeadCaptureRequest,
    workspace: Workspace = Depends(get_workspace_from_slug),
    db: AsyncSession = Depends(get_db),
):
    """Capture lead from widget form."""
    from sqlalchemy import select

    # Verify conversation exists
    result = await db.execute(
        select(Conversation).where(
            Conversation.id == request.conversation_id,
            Conversation.workspace_id == workspace.id,
        )
    )
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    if not request.consent:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="GDPR consent required",
        )

    # TODO: Create lead record
    conversation.has_lead = True
    await db.commit()

    return {"data": {"success": True, "message": "Thanks! We'll contact you soon."}}


# Authenticated Dashboard Endpoints
@router.get("/conversations", response_model=ConversationListResponse)
async def list_conversations(
    workspace: Workspace = Depends(get_authenticated_workspace),
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status_filter: str | None = Query(None, alias="status"),
    language: str | None = None,
):
    """List conversations for dashboard."""
    from sqlalchemy import select

    query = select(Conversation).where(Conversation.workspace_id == workspace.id)

    if status_filter:
        query = query.where(Conversation.status == status_filter)
    if language:
        query = query.where(Conversation.language == language)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)

    # Get paginated results
    query = query.order_by(Conversation.last_message_at.desc()).offset((page - 1) * limit).limit(limit)
    result = await db.execute(query)
    conversations = result.scalars().all()

    return ConversationListResponse(
        data=conversations,
        meta={
            "page": page,
            "limit": limit,
            "total": total,
            "total_pages": (total + limit - 1) // limit,
        },
    )


@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: UUID,
    workspace: Workspace = Depends(get_authenticated_workspace),
    db: AsyncSession = Depends(get_db),
):
    """Get conversation with messages."""
    from sqlalchemy import select

    result = await db.execute(
        select(Conversation)
        .options(selectinload(Conversation.messages))
        .where(
            Conversation.id == conversation_id,
            Conversation.workspace_id == workspace.id,
        )
    )
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    return conversation


@router.post("/conversations/{conversation_id}/reset")
async def reset_conversation(
    conversation_id: UUID,
    workspace: Workspace = Depends(get_authenticated_workspace),
    db: AsyncSession = Depends(get_db),
):
    """Reset conversation (mark as closed, start new session)."""
    from sqlalchemy import select
    from datetime import datetime, timezone

    result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.workspace_id == workspace.id,
        )
    )
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    conversation.status = "closed"
    conversation.closed_at = datetime.now(timezone.utc)
    await db.commit()

    return {"data": {"success": True, "message": "Conversation reset"}}