"""
Brainly API - Embedding Service

Jina AI embeddings via OpenAI-compatible client.
"""
from typing import Any
from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from ..config import get_settings


class EmbeddingClient:
    """Embedding client for Jina AI."""

    def __init__(self):
        self.settings = get_settings()
        self.client = AsyncOpenAI(
            api_key=self.settings.JINA_AI_API_KEY,
            base_url=self.settings.JINA_AI_BASE_URL,
            timeout=60.0,
        ) if self.settings.JINA_AI_API_KEY else None

    @retry(
        wait=wait_exponential(multiplier=1, min=1, max=10),
        stop=stop_after_attempt(3),
        retry=retry_if_exception_type(Exception),
    )
    async def create_embeddings(
        self,
        texts: list[str],
        model: str | None = None,
    ) -> list[list[float]]:
        """
        Create embeddings for a list of texts.

        Returns list of embeddings (1024 dimensions for jina-embeddings-v3).
        """
        if not self.client:
            raise RuntimeError("Jina AI API key not configured")

        model = model or self.settings.JINA_AI_MODEL

        # Process in batches to avoid rate limits
        batch_size = 32
        all_embeddings = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            response = await self.client.embeddings.create(
                model=model,
                input=batch,
                encoding_format="float",
            )
            batch_embeddings = [item.embedding for item in response.data]
            all_embeddings.extend(batch_embeddings)

        return all_embeddings

    async def create_embedding(self, text: str, model: str | None = None) -> list[float]:
        """Create embedding for a single text."""
        embeddings = await self.create_embeddings([text], model)
        return embeddings[0]


# Global instance
_embedding_client: EmbeddingClient | None = None


def get_embedding_client() -> EmbeddingClient:
    """Get or create embedding client instance."""
    global _embedding_client
    if _embedding_client is None:
        _embedding_client = EmbeddingClient()
    return _embedding_client