"""
Brainly API - Weekly FAQ Generation Worker

Vercel Cron job handler for FAQ suggestion generation.
"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import get_settings
from ..database import get_session_factory, init_db
from ..models import Workspace
from ..services.faq_generator import run_weekly_faq_generation


async def handler(event: dict) -> dict:
    """Vercel Cron job handler - runs weekly FAQ generation."""
    settings = get_settings()

    try:
        await init_db(settings)
        await run_weekly_faq_generation()
        return {"statusCode": 200, "body": "Weekly FAQ generation completed"}
    except Exception as e:
        print(f"Weekly FAQ generation failed: {e}")
        return {"statusCode": 500, "body": str(e)}