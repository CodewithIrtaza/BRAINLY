"""
Brainly API - FastAPI Application Factory

Main entry point for the FastAPI application.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import get_settings
from .database import init_db, close_db
from .api.v1 import auth, workspaces, kb, chat, leads, analytics, faq
from .exceptions.handlers import register_exception_handlers


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    settings = get_settings()
    await init_db(settings)
    yield
    # Shutdown
    await close_db()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="Brainly API",
        description="AI Customer Support Agent Platform API",
        version="1.0.0",
        docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
        redoc_url="/redoc" if settings.ENVIRONMENT != "production" else None,
        lifespan=lifespan,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register exception handlers
    register_exception_handlers(app)

    # Include API routers
    app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
    app.include_router(workspaces.router, prefix="/api/v1/workspaces", tags=["workspaces"])
    app.include_router(kb.router, prefix="/api/v1/kb", tags=["knowledge-base"])
    app.include_router(chat.router, prefix="/api/v1/chat", tags=["chat"])
    app.include_router(leads.router, prefix="/api/v1/leads", tags=["leads"])
    app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["analytics"])
    app.include_router(faq.router, prefix="/api/v1/faq", tags=["faq"])

    # Health check endpoint
    @app.get("/health", tags=["health"])
    async def health_check():
        return {"status": "ok", "version": "1.0.0"}

    @app.get("/api/v1/health", tags=["health"])
    async def api_health_check():
        return {"status": "ok", "version": "1.0.0"}

    return app


# Create the app instance
app = create_app()