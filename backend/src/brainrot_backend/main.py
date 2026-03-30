"""ASGI application entrypoint."""

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI

from brainrot_backend.api.router import api_router
from brainrot_backend.core.config import get_settings
from brainrot_backend.db.session import close_database_engine, initialize_database_engine


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Initialize and dispose shared resources across app lifecycle."""
    initialize_database_engine()
    try:
        yield
    finally:
        await close_database_engine()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application instance."""
    settings = get_settings()

    application = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Backend API for BrainrotGen.",
        lifespan=lifespan,
    )
    application.include_router(api_router, prefix=settings.api_v1_prefix)
    return application


app = create_app()
