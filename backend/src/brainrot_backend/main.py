"""ASGI application entrypoint"""

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from brainrot_backend.api.router import api_router
from brainrot_backend.core.config import get_settings
from brainrot_backend.db.base import Base
from brainrot_backend.db.session import (
    close_database_engine,
    get_database_engine,
    initialize_database_engine,
)

import brainrot_backend.models  # noqa: F401  — register all ORM models


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Initialize DB engine and create tables on startup, dispose on shutdown"""
    settings = get_settings()
    if not settings.database_url:
        Path(settings.sqlite_file).parent.mkdir(parents=True, exist_ok=True)
    Path(settings.media_root).mkdir(parents=True, exist_ok=True)

    initialize_database_engine()
    engine = get_database_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    try:
        yield
    finally:
        await close_database_engine()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application instance"""
    settings = get_settings()

    application = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Backend API for BrainrotGen",
        lifespan=lifespan,
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.include_router(api_router, prefix=settings.api_v1_prefix)
    return application


app = create_app()
