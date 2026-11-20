"""
Brainly API - Lead Routes

Lead management endpoints.
"""
from typing import Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ....config import get_settings
from ....database import get_db
from ....models import Workspace, Lead
from ....schemas.lead import LeadResponse, LeadUpdate
from ....api.deps import get_authenticated_workspace

router = APIRouter()


@router.get("", response_model=list[LeadResponse])
async def list_leads(
    workspace: Workspace = Depends(get_authenticated_workspace),
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status_filter: str | None = Query(None, alias="status"),
):
    """List leads for the workspace."""
    from sqlalchemy import select

    query = select(Lead).where(Lead.workspace_id == workspace.id)

    if status_filter:
        query = query.where(Lead.status == status_filter)

    query = query.order_by(Lead.created_at.desc()).offset((page - 1) * limit).limit(limit)

    result = await db.execute(query)
    leads = result.scalars().all()
    return leads


@router.get("/{lead_id}", response_model=LeadResponse)
async def get_lead(
    lead_id: UUID,
    workspace: Workspace = Depends(get_authenticated_workspace),
    db: AsyncSession = Depends(get_db),
):
    """Get lead details."""
    from sqlalchemy import select

    result = await db.execute(
        select(Lead).where(
            Lead.id == lead_id,
            Lead.workspace_id == workspace.id,
        )
    )
    lead = result.scalar_one_or_none()

    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found",
        )

    return lead


@router.patch("/{lead_id}", response_model=LeadResponse)
async def update_lead(
    lead_id: UUID,
    data: LeadUpdate,
    workspace: Workspace = Depends(get_authenticated_workspace),
    db: AsyncSession = Depends(get_db),
):
    """Update lead status/notes."""
    from sqlalchemy import select

    result = await db.execute(
        select(Lead).where(
            Lead.id == lead_id,
            Lead.workspace_id == workspace.id,
        )
    )
    lead = result.scalar_one_or_none()

    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found",
        )

    if data.status is not None:
        lead.status = data.status
    if data.notes is not None:
        lead.notes = data.notes

    await db.commit()
    await db.refresh(lead)
    return lead