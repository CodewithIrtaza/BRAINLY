"""
Brainly API - LLM Service

NVIDIA NIM (primary) + Groq (fallback) via OpenAI-compatible client.
"""
from typing import Any
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletion, ChatCompletionChunk
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from ..config import get_settings


class LLMClient:
    """LLM client with primary (NIM) and fallback (Groq) providers."""

    def __init__(self):
        self.settings = get_settings()

        # Primary: NVIDIA NIM
        self.nim_client = AsyncOpenAI(
            api_key=self.settings.NVIDIA_NIM_API_KEY,
            base_url=self.settings.NVIDIA_NIM_BASE_URL,
            timeout=60.0,
        ) if self.settings.NVIDIA_NIM_API_KEY else None

        # Fallback: Groq
        self.groq_client = AsyncOpenAI(
            api_key=self.settings.GROQ_API_KEY,
            base_url=self.settings.GROQ_BASE_URL,
            timeout=30.0,
        ) if self.settings.GROQ_API_KEY else None

    @retry(
        wait=wait_exponential(multiplier=1, min=1, max=10),
        stop=stop_after_attempt(3),
        retry=retry_if_exception_type(Exception),
    )
    async def chat_completion(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float = 0.3,
        max_tokens: int = 2048,
        stream: bool = False,
    ) -> ChatCompletion | ChatCompletionChunk:
        """
        Get chat completion with automatic fallback.

        Tries NVIDIA NIM first, falls back to Groq on failure.
        """
        model = model or self.settings.NVIDIA_NIM_MODEL

        # Try NIM first
        if self.nim_client:
            try:
                return await self._nim_chat_completion(
                    messages=messages,
                    model=model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    stream=stream,
                )
            except Exception as e:
                # Log and fall back to Groq
                print(f"NIM failed, falling back to Groq: {e}")

        # Fallback to Groq
        if self.groq_client:
            try:
                return await self._groq_chat_completion(
                    messages=messages,
                    model=self.settings.GROQ_MODEL,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    stream=stream,
                )
            except Exception as e:
                raise RuntimeError(f"Both NIM and Groq failed: {e}")

        raise RuntimeError("No LLM provider configured")

    async def _nim_chat_completion(
        self,
        messages: list[dict[str, str]],
        model: str,
        temperature: float,
        max_tokens: int,
        stream: bool,
    ) -> ChatCompletion | ChatCompletionChunk:
        """Call NVIDIA NIM chat completion."""
        return await self.nim_client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=stream,
        )

    async def _groq_chat_completion(
        self,
        messages: list[dict[str, str]],
        model: str,
        temperature: float,
        max_tokens: int,
        stream: bool,
    ) -> ChatCompletion | ChatCompletionChunk:
        """Call Groq chat completion."""
        return await self.groq_client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=stream,
        )


# Global instance
_llm_client: LLMClient | None = None


def get_llm_client() -> LLMClient:
    """Get or create LLM client instance."""
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client