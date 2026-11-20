"""
Brainly API - FAQ Generator Service

Weekly job to analyze conversations and suggest FAQ entries.
"""
from typing import Any
from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import get_settings
from ..models import FAQSuggestion, Conversation, Message
from ..services.llm import get_llm_client


class FAQGenerator:
    """Generate FAQ suggestions from conversation analysis."""

    def __init__(self):
        self.settings = get_settings()
        self.llm_client = get_llm_client()

    async def generate_suggestions(
        self,
        db: AsyncSession,
        workspace_id: UUID,
        lookback_days: int = 7,
    ) -> list[FAQSuggestion]:
        """
        Analyze recent conversations and generate FAQ suggestions.

        Runs as a weekly cron job.
        """
        # Get recent conversations with high message counts
        from datetime import datetime, timedelta, timezone
        cutoff = datetime.now(timezone.utc) - timedelta(days=lookback_days)

        # Find conversations with repeated questions
        # This is a simplified version - in production, use clustering
        result = await db.execute(
            select(Conversation)
            .where(
                Conversation.workspace_id == workspace_id,
                Conversation.started_at >= cutoff,
                Conversation.status.in_(["active", "closed"]),
            )
            .order_by(Conversation.message_count.desc())
            .limit(50)
        )
        conversations = result.scalars().all()

        if not conversations:
            return []

        # Get messages from these conversations
        conv_ids = [c.id for c in conversations]
        result = await db.execute(
            select(Message)
            .where(
                Message.conversation_id.in_(conv_ids),
                Message.role == "user",
            )
            .order_by(Message.created_at)
        )
        user_messages = result.scalars().all()

        # Group similar questions (simplified - use LLM in production)
        questions = [m.content for m in user_messages if len(m.content) > 10]
        if not questions:
            return []

        # Use LLM to cluster and generate FAQ suggestions
        suggestions = await self._generate_faq_from_questions(
            workspace_id, questions, conv_ids
        )

        # Save suggestions
        for suggestion in suggestions:
            db.add(suggestion)

        await db.commit()
        return suggestions

    async def _generate_faq_from_questions(
        self,
        workspace_id: UUID,
        questions: list[str],
        source_conversation_ids: list[UUID],
    ) -> list[FAQSuggestion]:
        """Use LLM to generate FAQ from questions."""
        # Deduplicate similar questions
        unique_questions = list(dict.fromkeys(questions))[:20]

        prompt = f"""Analyze these customer questions and identify 3-5 common topics 
that would make good FAQ entries. For each topic, provide:
1. A clear, concise question
2. A helpful answer based on general knowledge
3. Confidence score (0.0-1.0)

Questions:
{chr(10).join(f"- {q}" for q in unique_questions)}

Return as JSON array: [{{"question": "...", "answer": "...", "confidence": 0.8}}]"""

        try:
            response = await self.llm_client.chat_completion(
                messages=[
                    {"role": "system", "content": "You are an FAQ generation assistant. Return only valid JSON."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=1500,
            )

            import json
            content = response.choices[0].message.content
            faq_data = json.loads(content)

            suggestions = []
            for item in faq_data[:5]:  # Limit to 5 suggestions
                suggestion = FAQSuggestion(
                    workspace_id=workspace_id,
                    question=item["question"],
                    answer=item["answer"],
                    source_conversation_ids=source_conversation_ids,
                    confidence=item.get("confidence", 0.7),
                    status="pending",
                )
                suggestions.append(suggestion)

            return suggestions
        except Exception as e:
            print(f"FAQ generation failed: {e}")
            return []


async def run_weekly_faq_generation():
    """Entry point for Vercel Cron job."""
    from ..database import get_session_factory, init_db
    from ..config import get_settings

    settings = get_settings()
    await init_db(settings)

    factory = get_session_factory()
    async with factory() as db:
        # Get all active workspaces
        from ..models import Workspace
        result = await db.execute(
            select(Workspace).where(Workspace.deleted_at.is_(None))
        )
        workspaces = result.scalars().all()

        generator = FAQGenerator()
        for workspace in workspaces:
            try:
                await generator.generate_suggestions(db, workspace.id)
            except Exception as e:
                print(f"FAQ generation failed for workspace {workspace.id}: {e}")


def get_faq_generator() -> FAQGenerator:
    """Get FAQ generator instance."""
    return FAQGenerator()