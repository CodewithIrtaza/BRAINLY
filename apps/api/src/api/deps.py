"""
Brainly API - FastAPI Dependencies

Authentication, workspace isolation, and common dependencies.
"""
from typing import Optional
from uuid import UUID
from fastapi import Depends, Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import get_settings
from ..database import get_db
from ..models import Workspace


class AuthContext:
    """Authentication context from JWT."""
    def __init__(
        self,
        user_id: UUID,
        workspace_id: Optional[UUID] = None,
        workspace_slug: Optional[str] = None,
    ):
        self.user_id = user_id
        self.workspace_id = workspace_id
        self.workspace_slug = workspace_slug


async def get_current_user(
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db),
) -> AuthContext:
    """
    Extract user identity from Supabase JWT.

    In production, this should verify the JWT signature using SUPABASE_JWT_SECRET.
    For now, we extract the user_id from the token payload (simplified).
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header",
        )

    token = authorization.replace("Bearer ", "")

    # TODO: Implement proper JWT verification with Supabase
    # For now, return a mock context for development
    # In production: decode and verify JWT, extract user_id and workspace claims
    settings = get_settings()

    if settings.ENVIRONMENT == "development":
        # Return a mock user for development
        from uuid import uuid4
        return AuthContext(user_id=uuid4())

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication not configured for production",
    )


async def get_workspace_from_slug(
    workspace_slug: str,
    db: AsyncSession = Depends(get_db),
) -> Workspace:
    """Get workspace by slug (for public widget endpoints)."""
    from sqlalchemy import select

    result = await db.execute(
        select(Workspace).where(Workspace.slug == workspace_slug, Workspace.deleted_at.is_(None))
    )
    workspace = result.scalar_one_or_none()

    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found",
        )

    return workspace


async def get_authenticated_workspace(
    auth: AuthContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Workspace:
    """Get workspace for authenticated user (enforces ownership)."""
    from sqlalchemy import select

    if not auth.workspace_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Workspace context required",
        )

    result = await db.execute(
        select(Workspace).where(
            Workspace.id == auth.workspace_id,
            Workspace.deleted_at.is_(None),
        )
    )
    workspace = result.scalar_one_or_none()

    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found",
        )

    return workspace


def get_rate_limit_key(request: Request) -> str:
    """Generate rate limit key from request."""
    # Use workspace slug for widget endpoints, user ID for authenticated endpoints
    return request.client.host if request.client else "unknown"