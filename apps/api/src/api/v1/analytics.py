"""
Brainly API - Analytics Routes

Analytics and dashboard metrics endpoints.
"""
from typing import Any
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ....config import get_settings
from ....database import get_db
from ....models import Workspace, Conversation, Message, Lead, KBSource, KBChunk
from ....schemas.analytics import AnalyticsOverviewResponse
from ....api.deps import get_authenticated_workspace

router = APIRouter()


@router.get("/overview", response_model=AnalyticsOverviewResponse)
async def get_analytics_overview(
    workspace: Workspace = Depends(get_authenticated_workspace),
    db: AsyncSession = Depends(get_db),
):
    """Get analytics overview for dashboard."""
    settings = get_settings()

    if settings.ENVIRONMENT == "development":
        return AnalyticsOverviewResponse(
            total_conversations=0,
            conversations_today=0,
            conversations_this_week=0,
            conversations_this_month=0,
            resolution_rate=0.0,
            fallback_rate=0.0,
            avg_response_time_ms=0.0,
            total_leads=0,
            leads_this_week=0,
            kb_sources_count=0,
            kb_chunks_count=0,
        )

    # Total conversations
    total_conversations = await db.scalar(
        select(func.count(Conversation.id)).where(Conversation.workspace_id == workspace.id)
    )

    # Conversations today/week/month
    from datetime import datetime, timedelta, timezone
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = now - timedelta(days=now.weekday())
    week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    conversations_today = await db.scalar(
        select(func.count(Conversation.id)).where(
            Conversation.workspace_id == workspace.id,
            Conversation.started_at >= today_start,
        )
    )
    conversations_this_week = await db.scalar(
        select(func.count(Conversation.id)).where(
            Conversation.workspace_id == workspace.id,
            Conversation.started_at >= week_start,
        )
    )
    conversations_this_month = await db.scalar(
        select(func.count(Conversation.id)).where(
            Conversation.workspace_id == workspace.id,
            Conversation.started_at >= month_start,
        )
    )

    # Resolution rate (conversations without escalation)
    total_conv = total_conversations or 1
    escalated = await db.scalar(
        select(func.count(Conversation.id)).where(
            Conversation.workspace_id == workspace.id,
            Conversation.status == "escalated",
        )
    )
    resolution_rate = ((total_conv - escalated) / total_conv) * 100

    # Fallback rate
    total_messages = await db.scalar(
        select(func.count(Message.id))
        .select_from(Message)
        .join(Conversation)
        .where(Conversation.workspace_id == workspace.id)
    ) or 1
    fallback_messages = await db.scalar(
        select(func.count(Message.id))
        .select_from(Message)
        .join(Conversation)
        .where(
            Conversation.workspace_id == workspace.id,
            Message.is_fallback == True,
        )
    )
    fallback_rate = (fallback_messages / total_messages) * 100

    # Average response time (placeholder)
    avg_response_time_ms = 0.0

    # Leads
    total_leads = await db.scalar(
        select(func.count(Lead.id)).where(Lead.workspace_id == workspace.id)
    )
    leads_this_week = await db.scalar(
        select(func.count(Lead.id)).where(
            Lead.workspace_id == workspace.id,
            Lead.created_at >= week_start,
        )
    )

    # KB stats
    kb_sources_count = await db.scalar(
        select(func.count(KBSource.id)).where(
            KBSource.workspace_id == workspace.id,
            KBSource.status == "ready",
        )
    )
    kb_chunks_count = await db.scalar(
        select(func.count(KBChunk.id)).where(KBChunk.workspace_id == workspace.id)
    )

    return AnalyticsOverviewResponse(
        total_conversations=total_conversations or 0,
        conversations_today=conversations_today or 0,
        conversations_this_week=conversations_this_week or 0,
        conversations_this_month=conversations_this_month or 0,
        resolution_rate=round(resolution_rate, 2),
        fallback_rate=round(fallback_rate, 2),
        avg_response_time_ms=avg_response_time_ms,
        total_leads=total_leads or 0,
        leads_this_week=leads_this_week or 0,
        kb_sources_count=kb_sources_count or 0,
        kb_chunks_count=kb_chunks_count or 0,
    )