"""
Brainly API - Knowledge Base Routes

KB source management endpoints.
"""
from typing import Any
from uuid import UUID
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ....config import get_settings
from ....database import get_db
from ....models import Workspace, KBSource
from ....schemas.kb import (
    KBSourceCreate,
    KBSourceUpdate,
    KBSourceResponse,
    FAQEntryCreate,
    FAQBulkCreate,
)
from ....api.deps import get_authenticated_workspace

router = APIRouter()


@router.get("/sources", response_model=list[KBSourceResponse])
async def list_kb_sources(
    workspace: Workspace = Depends(get_authenticated_workspace),
    db: AsyncSession = Depends(get_db),
    status_filter: str | None = Query(None, alias="status"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """List KB sources for the workspace."""
    from sqlalchemy import select

    query = select(KBSource).where(KBSource.workspace_id == workspace.id)

    if status_filter:
        query = query.where(KBSource.status == status_filter)

    query = query.order_by(KBSource.created_at.desc()).limit(limit).offset(offset)

    result = await db.execute(query)
    sources = result.scalars().all()
    return sources


@router.post("/sources", response_model=KBSourceResponse, status_code=status.HTTP_201_CREATED)
async def create_kb_source(
    data: KBSourceCreate,
    workspace: Workspace = Depends(get_authenticated_workspace),
    db: AsyncSession = Depends(get_db),
):
    """Create a new KB source (metadata only - file upload handled separately)."""
    settings = get_settings()

    if settings.ENVIRONMENT == "development":
        # Return mock response
        from uuid import uuid4
        from datetime import datetime, timezone
        return KBSourceResponse(
            id=uuid4(),
            workspace_id=workspace.id,
            type=data.type,
            filename=data.filename,
            url=data.url,
            status="pending",
            error_message=None,
            chunk_count=0,
            token_count=0,
            file_size=None,
            storage_path=None,
            meta=data.meta,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            processed_at=None,
        )

    source = KBSource(
        workspace_id=workspace.id,
        type=data.type,
        filename=data.filename,
        url=data.url,
        meta=data.meta,
        status="pending",
    )
    db.add(source)
    await db.commit()
    await db.refresh(source)
    return source


@router.post("/sources/upload", response_model=KBSourceResponse, status_code=status.HTTP_201_CREATED)
async def upload_kb_source(
    file: UploadFile = File(...),
    type: str = Query(..., pattern=r"^(pdf|txt)$"),
    workspace: Workspace = Depends(get_authenticated_workspace),
    db: AsyncSession = Depends(get_db),
):
    """Upload a PDF/TXT file as KB source."""
    settings = get_settings()

    # Validate file type
    allowed_types = {"pdf": "application/pdf", "txt": "text/plain"}
    if file.content_type not in allowed_types.values():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed: PDF, TXT",
        )

    # Check file size
    max_size = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    content = await file.read()
    if len(content) > max_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Max size: {settings.MAX_FILE_SIZE_MB}MB",
        )

    if settings.ENVIRONMENT == "development":
        from uuid import uuid4
        from datetime import datetime, timezone
        return KBSourceResponse(
            id=uuid4(),
            workspace_id=workspace.id,
            type=type,
            filename=file.filename,
            status="processing",
            error_message=None,
            chunk_count=0,
            token_count=0,
            file_size=len(content),
            storage_path=None,
            meta={},
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            processed_at=None,
        )

    # TODO: Upload to Supabase Storage, create source record, trigger processing job
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="File upload processing not implemented yet",
    )


@router.get("/sources/{source_id}", response_model=KBSourceResponse)
async def get_kb_source(
    source_id: UUID,
    workspace: Workspace = Depends(get_authenticated_workspace),
    db: AsyncSession = Depends(get_db),
):
    """Get KB source details."""
    from sqlalchemy import select

    result = await db.execute(
        select(KBSource).where(
            KBSource.id == source_id,
            KBSource.workspace_id == workspace.id,
        )
    )
    source = result.scalar_one_or_none()

    if not source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="KB source not found",
        )

    return source


@router.post("/sources/{source_id}/reprocess", response_model=KBSourceResponse)
async def reprocess_kb_source(
    source_id: UUID,
    workspace: Workspace = Depends(get_authenticated_workspace),
    db: AsyncSession = Depends(get_db),
):
    """Retry processing a failed KB source."""
    from sqlalchemy import select

    result = await db.execute(
        select(KBSource).where(
            KBSource.id == source_id,
            KBSource.workspace_id == workspace.id,
        )
    )
    source = result.scalar_one_or_none()

    if not source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="KB source not found",
        )

    if source.status not in ("failed", "pending"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only reprocess failed or pending sources",
        )

    source.status = "processing"
    source.error_message = None
    await db.commit()
    await db.refresh(source)

    # TODO: Trigger background processing job
    return source


@router.delete("/sources/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_kb_source(
    source_id: UUID,
    workspace: Workspace = Depends(get_authenticated_workspace),
    db: AsyncSession = Depends(get_db),
):
    """Delete KB source and its vectors."""
    from sqlalchemy import select

    result = await db.execute(
        select(KBSource).where(
            KBSource.id == source_id,
            KBSource.workspace_id == workspace.id,
        )
    )
    source = result.scalar_one_or_none()

    if not source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="KB source not found",
        )

    await db.delete(source)
    await db.commit()


# FAQ Routes
@router.post("/faq", response_model=list[KBSourceResponse], status_code=status.HTTP_201_CREATED)
async def bulk_create_faq(
    data: FAQBulkCreate,
    workspace: Workspace = Depends(get_authenticated_workspace),
    db: AsyncSession = Depends(get_db),
):
    """Bulk create FAQ entries as KB sources."""
    settings = get_settings()

    if settings.ENVIRONMENT == "development":
        from uuid import uuid4
        from datetime import datetime, timezone
        return [
            KBSourceResponse(
                id=uuid4(),
                workspace_id=workspace.id,
                type="faq",
                filename=None,
                status="ready",
                error_message=None,
                chunk_count=len(data.entries),
                token_count=0,
                file_size=None,
                storage_path=None,
                meta={"entries": [e.model_dump() for e in data.entries]},
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                processed_at=datetime.now(timezone.utc),
            )
        ]

    # TODO: Implement FAQ creation
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="FAQ creation not implemented yet",
    )