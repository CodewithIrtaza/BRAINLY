"""
Brainly API - FAQ Suggestion Routes

FAQ auto-generation and management endpoints.
"""
from typing import Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ....config import get_settings
from ....database import get_db
from ....models import Workspace, FAQSuggestion
from ....schemas.faq import FAQSuggestionResponse, FAQSuggestionAction
from ....api.deps import get_authenticated_workspace

router = APIRouter()


@router.get("/suggestions", response_model=list[FAQSuggestionResponse])
async def list_faq_suggestions(
    workspace: Workspace = Depends(get_authenticated_workspace),
    db: AsyncSession = Depends(get_db),
    status_filter: str | None = Query(None, alias="status"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """List FAQ suggestions for the workspace."""
    from sqlalchemy import select

    query = select(FAQSuggestion).where(FAQSuggestion.workspace_id == workspace.id)

    if status_filter:
        query = query.where(FAQSuggestion.status == status_filter)

    query = query.order_by(FAQSuggestion.created_at.desc()).limit(limit).offset(offset)

    result = await db.execute(query)
    suggestions = result.scalars().all()
    return suggestions


@router.post("/suggestions/{suggestion_id}/approve", response_model=FAQSuggestionResponse)
async def approve_faq_suggestion(
    suggestion_id: UUID,
    workspace: Workspace = Depends(get_authenticated_workspace),
    db: AsyncSession = Depends(get_db),
):
    """Approve FAQ suggestion and add to knowledge base."""
    from sqlalchemy import select
    from datetime import datetime, timezone

    result = await db.execute(
        select(FAQSuggestion).where(
            FAQSuggestion.id == suggestion_id,
            FAQSuggestion.workspace_id == workspace.id,
        )
    )
    suggestion = result.scalar_one_or_none()

    if not suggestion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="FAQ suggestion not found",
        )

    if suggestion.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only approve pending suggestions",
        )

    suggestion.status = "approved"
    suggestion.reviewed_at = datetime.now(timezone.utc)
    # TODO: Get reviewer from auth context
    # suggestion.reviewed_by = auth.user_id

    # TODO: Create KB source with FAQ entry
    suggestion.status = "added"
    await db.commit()
    await db.refresh(suggestion)
    return suggestion


@router.post("/suggestions/{suggestion_id}/reject", response_model=FAQSuggestionResponse)
async def reject_faq_suggestion(
    suggestion_id: UUID,
    workspace: Workspace = Depends(get_authenticated_workspace),
    db: AsyncSession = Depends(get_db),
):
    """Reject FAQ suggestion."""
    from sqlalchemy import select
    from datetime import datetime, timezone

    result = await db.execute(
        select(FAQSuggestion).where(
            FAQSuggestion.id == suggestion_id,
            FAQSuggestion.workspace_id == workspace.id,
        )
    )
    suggestion = result.scalar_one_or_none()

    if not suggestion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="FAQ suggestion not found",
        )

    if suggestion.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only reject pending suggestions",
        )

    suggestion.status = "rejected"
    suggestion.reviewed_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(suggestion)
    return suggestion