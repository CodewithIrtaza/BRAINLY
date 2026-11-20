"""
Brainly API - Custom Exceptions
"""
from .http_exceptions import (
    BrainlyException,
    NotFoundError,
    ValidationError,
    AuthenticationError,
    AuthorizationError,
    RateLimitError,
    ExternalServiceError,
)

__all__ = [
    "BrainlyException",
    "NotFoundError",
    "ValidationError",
    "AuthenticationError",
    "AuthorizationError",
    "RateLimitError",
    "ExternalServiceError",
]