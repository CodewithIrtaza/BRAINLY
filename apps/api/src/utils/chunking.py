"""
Brainly API - Text Chunking Utilities

Split text into overlapping chunks for embedding.
"""
import tiktoken
from typing import Any


# Tokenizer for OpenAI-compatible models
_encoding = tiktoken.get_encoding("cl100k_base")


def count_tokens(text: str) -> int:
    """Count tokens in text."""
    return len(_encoding.encode(text))


def chunk_text(
    text: str,
    max_tokens: int = 500,
    overlap_tokens: int = 50,
) -> list[dict[str, Any]]:
    """
    Split text into overlapping chunks.

    Returns list of chunks with token counts.
    """
    if not text or not text.strip():
        return []

    tokens = _encoding.encode(text)
    chunks = []

    start = 0
    while start < len(tokens):
        end = min(start + max_tokens, len(tokens))
        chunk_tokens = tokens[start:end]
        chunk_text = _encoding.decode(chunk_tokens)

        chunks.append({
            "content": chunk_text,
            "token_count": len(chunk_tokens),
            "start_token": start,
            "end_token": end,
        })

        if end >= len(tokens):
            break

        # Move start forward with overlap
        start = end - overlap_tokens
        if start < 0:
            start = 0

    return chunks


def chunk_by_paragraphs(
    text: str,
    max_tokens: int = 500,
    overlap_tokens: int = 50,
) -> list[dict[str, Any]]:
    """
    Split text by paragraphs, then chunk if needed.

    Better preserves semantic boundaries.
    """
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks = []

    current_chunk = ""
    current_tokens = 0

    for para in paragraphs:
        para_tokens = count_tokens(para)

        if para_tokens > max_tokens:
            # Paragraph too large, split it
            if current_chunk:
                chunks.append({
                    "content": current_chunk,
                    "token_count": current_tokens,
                })
                current_chunk = ""
                current_tokens = 0

            # Split large paragraph
            sub_chunks = chunk_text(para, max_tokens, overlap_tokens)
            chunks.extend(sub_chunks)
        elif current_tokens + para_tokens > max_tokens:
            # Current chunk would exceed limit
            if current_chunk:
                chunks.append({
                    "content": current_chunk,
                    "token_count": current_tokens,
                })
            current_chunk = para
            current_tokens = para_tokens
        else:
            # Add to current chunk
            if current_chunk:
                current_chunk += "\n\n" + para
            else:
                current_chunk = para
            current_tokens += para_tokens

    if current_chunk:
        chunks.append({
            "content": current_chunk,
            "token_count": current_tokens,
        })

    return chunks