"""
Brainly API - HTTP Exception Classes

Custom exception classes with error codes for consistent error responses.
"""
from typing import Any
from fastapi import HTTPException, status


class BrainlyException(HTTPException):
    """Base exception for Brainly API errors."""

    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(
            status_code=status_code,
            detail={"code": code, "message": message, "details": details or {}},
        )
        self.code = code
        self.message = message
        self.details = details or {}


class NotFoundError(BrainlyException):
    """Resource not found."""

    def __init__(self, resource: str, identifier: str | int, details: dict[str, Any] | None = None):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            code="NOT_FOUND",
            message=f"{resource} not found",
            details={"resource": resource, "identifier": str(identifier), **(details or {})},
        )


class ValidationError(BrainlyException):
    """Request validation error."""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
            message=message,
            details=details,
        )


class AuthenticationError(BrainlyException):
    """Authentication required or failed."""

    def __init__(self, message: str = "Authentication required", details: dict[str, Any] | None = None):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="UNAUTHORIZED",
            message=message,
            details=details,
        )


class AuthorizationError(BrainlyException):
    """Access denied / insufficient permissions."""

    def __init__(self, message: str = "Access denied", details: dict[str, Any] | None = None):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            code="FORBIDDEN",
            message=message,
            details=details,
        )


class RateLimitError(BrainlyException):
    """Rate limit exceeded."""

    def __init__(self, message: str = "Rate limit exceeded", details: dict[str, Any] | None = None):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            code="RATE_LIMITED",
            message=message,
            details=details,
        )


class ExternalServiceError(BrainlyException):
    """External service (LLM, embeddings, email) error."""

    def __init__(self, service: str, message: str, details: dict[str, Any] | None = None):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            code="EXTERNAL_SERVICE_ERROR",
            message=f"{service}: {message}",
            details={"service": service, **(details or {})},
        )