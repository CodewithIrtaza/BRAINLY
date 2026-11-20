"""
Brainly API - RAG Pipeline

Retrieval-Augmented Generation pipeline for chat responses.
"""
from typing import Any
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pgvector.sqlalchemy import Vector

from ..config import get_settings
from ..models import KBChunk, Workspace
from ..services.embedding import get_embedding_client
from ..services.llm import get_llm_client


SIMILARITY_THRESHOLD = 0.7
MAX_CHUNKS = 5


class RAGPipeline:
    """RAG pipeline for answering questions from knowledge base."""

    def __init__(self):
        self.settings = get_settings()
        self.embedding_client = get_embedding_client()
        self.llm_client = get_llm_client()

    async def answer(
        self,
        workspace_id: UUID,
        question: str,
        agent_config: dict,
        session_id: str | None = None,
        language: str = "en",
    ) -> dict[str, Any]:
        """
        Answer a question using RAG.

        Returns dict with answer, citations, and metadata.
        """
        # 1. Generate query embedding
        query_embedding = await self.embedding_client.create_embedding(question)

        # 2. Retrieve relevant chunks
        chunks = await self._retrieve_chunks(workspace_id, query_embedding)

        # 3. Build context and generate answer
        if chunks and chunks[0].get("score", 0) >= SIMILARITY_THRESHOLD:
            return await self._generate_with_context(question, chunks, agent_config, language)
        else:
            return await self._generate_fallback(question, agent_config, language)

    async def _retrieve_chunks(
        self,
        workspace_id: UUID,
        query_embedding: list[float],
    ) -> list[dict[str, Any]]:
        """Retrieve top-k relevant chunks using vector similarity search."""
        from ..database import get_session_factory

        factory = get_session_factory()
        async with factory() as session:
            # Use cosine similarity search
            result = await session.execute(
                select(
                    KBChunk.id,
                    KBChunk.content,
                    KBChunk.metadata,
                    KBChunk.content_hash,
                    (1 - KBChunk.embedding.cosine_distance(query_embedding)).label("score"),
                )
                .where(
                    KBChunk.workspace_id == workspace_id,
                    KBChunk.embedding.is_not(None),
                )
                .order_by(KBChunk.embedding.cosine_distance(query_embedding))
                .limit(MAX_CHUNKS)
            )
            rows = result.all()

            return [
                {
                    "chunk_id": row.id,
                    "content": row.content,
                    "metadata": row.metadata,
                    "content_hash": row.content_hash,
                    "score": float(row.score),
                }
                for row in rows
            ]

    async def _generate_with_context(
        self,
        question: str,
        chunks: list[dict[str, Any]],
        agent_config: dict,
        language: str,
    ) -> dict[str, Any]:
        """Generate answer using retrieved context."""
        # Build context from chunks
        context_parts = []
        citations = []

        for i, chunk in enumerate(chunks):
            context_parts.append(f"[Source {i+1}]\n{chunk['content']}")
            citations.append({
                "chunk_id": str(chunk["chunk_id"]),
                "preview": chunk["content"][:200],
                "score": chunk["score"],
            })

        context = "\n\n".join(context_parts)

        # Build system prompt
        system_prompt = self._build_system_prompt(agent_config, context, language)

        # Generate response
        response = await self.llm_client.chat_completion(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question},
            ],
            model=agent_config.get("model"),
            temperature=agent_config.get("temperature", 0.3),
            max_tokens=agent_config.get("max_tokens", 2048),
            stream=False,
        )

        return {
            "content": response.choices[0].message.content,
            "citations": citations,
            "fallback": False,
            "model_used": response.model,
        }

    async def _generate_fallback(
        self,
        question: str,
        agent_config: dict,
        language: str,
    ) -> dict[str, Any]:
        """Generate fallback response when no relevant context found."""
        fallback_msg = agent_config.get(
            "fallback_msg",
            "I don't have that information. Would you like to talk to a human?"
        )

        system_prompt = f"""You are a helpful customer support assistant.
Language: {language}
When you don't know the answer, use this fallback message: "{fallback_msg}"
Be polite and offer to escalate to a human agent."""

        response = await self.llm_client.chat_completion(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question},
            ],
            model=agent_config.get("model"),
            temperature=0.5,
            max_tokens=500,
            stream=False,
        )

        return {
            "content": response.choices[0].message.content,
            "citations": [],
            "fallback": True,
            "model_used": response.model,
        }

    def _build_system_prompt(self, agent_config: dict, context: str, language: str) -> str:
        """Build system prompt with agent config and context."""
        name = agent_config.get("name", "Brainly Assistant")
        instructions = agent_config.get("instructions", "")
        language_names = {"en": "English", "ur": "Urdu", "ur-Roman": "Roman Urdu"}
        lang_name = language_names.get(language, "English")

        prompt = f"""You are {name}, a helpful customer support assistant.
Language: {lang_name} - ALWAYS respond in the same language/script as the user.

{instructions}

Use the following knowledge base context to answer the user's question.
Cite sources using [1], [2], etc. format.

Knowledge Base Context:
{context}

Guidelines:
- Answer based ONLY on the provided context
- If the context doesn't contain the answer, use the fallback message
- Be concise and helpful
- Always respond in {lang_name}"""

        return prompt


def get_rag_pipeline() -> RAGPipeline:
    """Get RAG pipeline instance."""
    return RAGPipeline()