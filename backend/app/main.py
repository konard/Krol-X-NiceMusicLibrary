"""FastAPI application entry point."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.auth import router as auth_router
from app.api.health import router as health_router
from app.api.songs import router as songs_router
from app.api.stats import router as stats_router
from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan context manager."""
    # Startup
    yield
    # Shutdown


def create_app() -> FastAPI:
    """Application factory."""
    app = FastAPI(
        title=settings.APP_NAME,
        description="Personal music library with mood chains and smart recommendations",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(health_router, prefix=settings.API_V1_PREFIX, tags=["health"])
    app.include_router(
        auth_router, prefix=f"{settings.API_V1_PREFIX}/auth", tags=["auth"]
    )
    app.include_router(
        songs_router, prefix=f"{settings.API_V1_PREFIX}/songs", tags=["songs"]
    )
    app.include_router(
        stats_router, prefix=f"{settings.API_V1_PREFIX}/stats", tags=["stats"]
    )

    return app


app = create_app()
