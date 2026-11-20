"""
Brainly API - KB Processing Worker

Vercel Edge Function handler for KB source processing.
"""
import io
from uuid import UUID
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import get_settings
from ..database import get_session_factory, init_db
from ..models import KBSource, KBChunk
from ..services.embedding import get_embedding_client
from ..utils.pdf import extract_pdf_content
from ..utils.chunking import chunk_by_paragraphs


async def process_kb_source(source_id: UUID) -> None:
    """
    Process a KB source: extract text, chunk, embed, store vectors.

    Called by Vercel Cron or triggered via API.
    """
    settings = get_settings()
    await init_db(settings)

    factory = get_session_factory()
    async with factory() as db:
        # Get source
        result = await db.execute(
            select(KBSource).where(KBSource.id == source_id)
        )
        source = result.scalar_one_or_none()

        if not source:
            print(f"Source {source_id} not found")
            return

        # Update status to processing
        source.status = "processing"
        await db.commit()

        try:
            if settings.ENVIRONMENT == "development":
                # Mock processing for development
                from datetime import datetime, timezone
                source.status = "ready"
                source.chunk_count = 5
                source.token_count = 1000
                source.processed_at = datetime.now(timezone.utc)
                await db.commit()
                return

            # Download file from Supabase Storage
            # TODO: Implement actual download from Supabase Storage
            # For now, mock the file content
            file_bytes = b"Mock PDF content for development"

            # Extract content
            content_data = extract_pdf_content(file_bytes)
            text = content_data["text"]

            # Chunk text
            chunks = chunk_by_paragraphs(text, max_tokens=500, overlap_tokens=50)

            # Generate embeddings
            embedding_client = get_embedding_client()
            chunk_texts = [c["content"] for c in chunks]
            embeddings = await embedding_client.create_embeddings(chunk_texts)

            # Store chunks with embeddings
            total_tokens = 0
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                kb_chunk = KBChunk(
                    source_id=source.id,
                    workspace_id=source.workspace_id,
                    content=chunk["content"],
                    content_hash=f"{source.id}:{i}",
                    embedding=embedding,
                    metadata={
                        "page": 1,  # TODO: extract from pdfplumber
                        "chunk_index": i,
                        "token_count": chunk["token_count"],
                    },
                    token_count=chunk["token_count"],
                )
                db.add(kb_chunk)
                total_tokens += chunk["token_count"]

            # Update source status
            from datetime import datetime, timezone
            source.status = "ready"
            source.chunk_count = len(chunks)
            source.token_count = total_tokens
            source.processed_at = datetime.now(timezone.utc)

            await db.commit()
            print(f"Processed KB source {source_id}: {len(chunks)} chunks")

        except Exception as e:
            # Mark as failed
            source.status = "failed"
            source.error_message = str(e)
            await db.commit()
            print(f"KB processing failed for {source_id}: {e}")
            raise


async def handler(event: dict) -> dict:
    """Vercel Edge Function handler."""
    source_id = event.get("source_id")
    if not source_id:
        return {"statusCode": 400, "body": "Missing source_id"}

    try:
        await process_kb_source(UUID(source_id))
        return {"statusCode": 200, "body": "OK"}
    except Exception as e:
        return {"statusCode": 500, "body": str(e)}