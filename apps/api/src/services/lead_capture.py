"""
Brainly API - Lead Capture Service

Handle lead form submissions and validation.
"""
from typing import Any
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Lead, Conversation
from ..schemas.chat import LeadCaptureRequest


class LeadCaptureService:
    """Handle lead capture from chat widget."""

    async def capture_lead(
        self,
        db: AsyncSession,
        workspace_id: UUID,
        request: LeadCaptureRequest,
    ) -> Lead:
        """Capture and store a lead."""
        # Verify conversation belongs to workspace
        result = await db.execute(
            select(Conversation).where(
                Conversation.id == request.conversation_id,
                Conversation.workspace_id == workspace_id,
            )
        )
        conversation = result.scalar_one_or_none()

        if not conversation:
            raise ValueError("Conversation not found")

        if not request.consent:
            raise ValueError("GDPR consent required")

        # Create lead record
        lead = Lead(
            workspace_id=workspace_id,
            conversation_id=request.conversation_id,
            data=request.data,
            consent=request.consent,
            source="widget",
            status="new",
        )
        db.add(lead)

        # Update conversation
        conversation.has_lead = True

        await db.commit()
        await db.refresh(lead)
        return lead


def get_lead_capture_service() -> LeadCaptureService:
    """Get lead capture service instance."""
    return LeadCaptureService()