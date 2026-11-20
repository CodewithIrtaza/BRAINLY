"""
Brainly API - Workspace Routes

Workspace and agent configuration endpoints.
"""
from typing import Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ....config import get_settings
from ....database import get_db
from ....models import Workspace, Agent
from ....schemas.workspace import (
    WorkspaceCreate,
    WorkspaceUpdate,
    WorkspaceResponse,
    AgentConfigUpdate,
    AgentConfigResponse,
)
from ....api.deps import get_authenticated_workspace

router = APIRouter()


@router.get("", response_model=list[WorkspaceResponse])
async def list_workspaces(
    db: AsyncSession = Depends(get_db),
    auth_workspace: Workspace = Depends(get_authenticated_workspace),
):
    """List workspaces for the authenticated user."""
    settings = get_settings()

    if settings.ENVIRONMENT == "development":
        # Return the current workspace
        return [auth_workspace]

    # In production, query all workspaces where user is owner or member
    result = await db.execute(
        select(Workspace)
        .where(Workspace.deleted_at.is_(None))
        .order_by(Workspace.created_at.desc())
    )
    workspaces = result.scalars().all()
    return workspaces


@router.post("", response_model=WorkspaceResponse, status_code=status.HTTP_201_CREATED)
async def create_workspace(
    data: WorkspaceCreate,
    db: AsyncSession = Depends(get_db),
    auth_workspace: Workspace = Depends(get_authenticated_workspace),
):
    """Create a new workspace."""
    settings = get_settings()

    if settings.ENVIRONMENT == "development":
        # Return mock response
        return auth_workspace

    # Check slug uniqueness
    from sqlalchemy import select
    result = await db.execute(select(Workspace).where(Workspace.slug == data.slug))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Workspace slug already taken",
        )

    workspace = Workspace(
        name=data.name,
        slug=data.slug,
        owner_id=auth_workspace.owner_id,  # Use current user as owner
    )
    db.add(workspace)
    await db.flush()

    # Create default agent
    agent = Agent(workspace_id=workspace.id)
    db.add(agent)
    await db.commit()
    await db.refresh(workspace)

    return workspace


@router.get("/{workspace_id}", response_model=WorkspaceResponse)
async def get_workspace(
    workspace_id: UUID,
    db: AsyncSession = Depends(get_db),
    auth_workspace: Workspace = Depends(get_authenticated_workspace),
):
    """Get workspace details."""
    if auth_workspace.id != workspace_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )
    return auth_workspace


@router.patch("/{workspace_id}", response_model=WorkspaceResponse)
async def update_workspace(
    workspace_id: UUID,
    data: WorkspaceUpdate,
    db: AsyncSession = Depends(get_db),
    auth_workspace: Workspace = Depends(get_authenticated_workspace),
):
    """Update workspace settings."""
    if auth_workspace.id != workspace_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    if data.name is not None:
        auth_workspace.name = data.name
    if data.settings is not None:
        auth_workspace.settings = {**auth_workspace.settings, **data.settings}

    await db.commit()
    await db.refresh(auth_workspace)
    return auth_workspace


@router.delete("/{workspace_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workspace(
    workspace_id: UUID,
    db: AsyncSession = Depends(get_db),
    auth_workspace: Workspace = Depends(get_authenticated_workspace),
):
    """Soft delete workspace."""
    if auth_workspace.id != workspace_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    from datetime import datetime, timezone
    auth_workspace.deleted_at = datetime.now(timezone.utc)
    await db.commit()


# Agent Configuration Routes
@router.get("/{workspace_id}/agent", response_model=AgentConfigResponse)
async def get_agent_config(
    workspace_id: UUID,
    db: AsyncSession = Depends(get_db),
    auth_workspace: Workspace = Depends(get_authenticated_workspace),
):
    """Get agent configuration."""
    if auth_workspace.id != workspace_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    result = await db.execute(
        select(Agent).where(Agent.workspace_id == workspace_id)
    )
    agent = result.scalar_one_or_none()

    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found",
        )

    return agent


@router.patch("/{workspace_id}/agent", response_model=AgentConfigResponse)
async def update_agent_config(
    workspace_id: UUID,
    data: AgentConfigUpdate,
    db: AsyncSession = Depends(get_db),
    auth_workspace: Workspace = Depends(get_authenticated_workspace),
):
    """Update agent configuration."""
    if auth_workspace.id != workspace_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    result = await db.execute(
        select(Agent).where(Agent.workspace_id == workspace_id)
    )
    agent = result.scalar_one_or_none()

    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found",
        )

    # Update fields
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(agent, field, value)

    await db.commit()
    await db.refresh(agent)
    return agent