"""
Brainly API - Analytics Schemas

Pydantic models for analytics responses.
"""
from typing import Any
from pydantic import BaseModel, ConfigDict


class AnalyticsOverviewResponse(BaseModel):
    """Analytics overview for dashboard."""
    model_config = ConfigDict(from_attributes=True)

    total_conversations: int
    conversations_today: int
    conversations_this_week: int
    conversations_this_month: int
    resolution_rate: float
    fallback_rate: float
    avg_response_time_ms: float
    total_leads: int
    leads_this_week: int
    kb_sources_count: int
    kb_chunks_count: int