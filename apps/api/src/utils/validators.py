"""
Brainly API - Input Validators

Validation helpers for file uploads, URLs, etc.
"""
import re
from typing import Any
from urllib.parse import urlparse


def validate_file_type(filename: str, content_type: str, allowed_types: list[str]) -> bool:
    """Validate file type by extension and MIME type."""
    # Check extension
    ext = filename.lower().split(".")[-1] if "." in filename else ""
    allowed_exts = {"pdf", "txt", "md", "markdown"}

    if ext not in allowed_exts:
        return False

    # Check MIME type
    allowed_mimes = {
        "pdf": "application/pdf",
        "txt": "text/plain",
        "md": "text/markdown",
        "markdown": "text/markdown",
    }
    expected_mime = allowed_mimes.get(ext)
    if expected_mime and content_type != expected_mime:
        return False

    return True


def validate_file_size(size: int, max_size_mb: int = 10) -> bool:
    """Validate file size."""
    max_bytes = max_size_mb * 1024 * 1024
    return size <= max_bytes


def validate_url(url: str) -> bool:
    """Validate URL format."""
    try:
        result = urlparse(url)
        return all([result.scheme in ("http", "https"), result.netloc])
    except Exception:
        return False


def validate_workspace_slug(slug: str) -> bool:
    """Validate workspace slug format."""
    return bool(re.match(r"^[a-z0-9-]+$", slug)) and 1 <= len(slug) <= 100


def validate_language_code(code: str) -> bool:
    """Validate language code."""
    return code in {"en", "ur", "ur-Roman", "auto"}


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe storage."""
    # Remove path components
    filename = filename.split("/")[-1].split("\\")[-1]
    # Remove dangerous characters
    filename = re.sub(r"[^a-zA-Z0-9._-]", "_", filename)
    # Limit length
    if len(filename) > 255:
        name, ext = filename.rsplit(".", 1) if "." in filename else (filename, "")
        filename = name[:255 - len(ext) - 1] + ("." + ext if ext else "")
    return filename