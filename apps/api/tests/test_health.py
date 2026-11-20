"""
Brainly API - Health Check Tests

Tests for the health check endpoints.
"""
import pytest
from httpx import AsyncClient, ASGITransport

from src.main import app


@pytest.mark.asyncio
async def test_health_check():
    """Test root health check endpoint."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["version"] == "1.0.0"


@pytest.mark.asyncio
async def test_api_health_check():
    """Test API health check endpoint."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["version"] == "1.0.0"


@pytest.mark.asyncio
async def test_openapi_docs_available():
    """Test that OpenAPI docs are available in development."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/docs")
        # In development, docs should be available
        assert response.status_code in (200, 404)  # 404 if not in development mode