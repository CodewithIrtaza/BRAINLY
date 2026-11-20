"""
Brainly API - Auth Routes

Authentication endpoints (delegated to Supabase, backend validates JWT).
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ....config import get_settings
from ....database import get_db
from ....api.deps import AuthContext, get_current_user

router = APIRouter()


@router.post("/signup", status_code=status.HTTP_201_CREATED)
async def signup(
    email: str,
    password: str,
    workspace_name: str,
    workspace_slug: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Sign up a new user and create workspace.

    Note: Actual user creation is handled by Supabase Auth on the frontend.
    This endpoint creates the workspace after successful Supabase signup.
    """
    settings = get_settings()

    if settings.ENVIRONMENT == "development":
        # Return mock response for development
        from uuid import uuid4
        from datetime import datetime
        return {
            "data": {
                "user_id": str(uuid4()),
                "workspace_id": str(uuid4()),
                "message": "Workspace created. Please verify your email.",
            }
        }

    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Use Supabase Auth directly from frontend for signup",
    )


@router.post("/login")
async def login(email: str, password: str):
    """
    Login endpoint.

    Note: Actual login is handled by Supabase Auth on the frontend.
    """
    settings = get_settings()

    if settings.ENVIRONMENT == "development":
        return {
            "data": {
                "access_token": "mock-token",
                "token_type": "bearer",
                "expires_in": 3600,
            }
        }

    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Use Supabase Auth directly from frontend for login",
    )


@router.get("/me")
async def get_current_user_info(auth: AuthContext = Depends(get_current_user)):
    """Get current authenticated user info."""
    return {
        "data": {
            "user_id": str(auth.user_id),
            "workspace_id": str(auth.workspace_id) if auth.workspace_id else None,
        }
    }