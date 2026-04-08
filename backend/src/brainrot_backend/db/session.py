"""Async SQLite engine and session lifecycle helpers."""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from brainrot_backend.core.config import Settings, get_settings

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def initialize_database_engine(settings: Settings | None = None) -> AsyncEngine:
    """Initialize singleton async SQLAlchemy engine/session factory."""
    global _engine, _session_factory

    if _engine is not None and _session_factory is not None:
        return _engine

    active_settings = settings or get_settings()
    _engine = create_async_engine(
        active_settings.resolved_database_url,
        echo=active_settings.is_development,
        pool_pre_ping=True,
    )
    _session_factory = async_sessionmaker(
        bind=_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    return _engine


def get_database_engine() -> AsyncEngine:
    """Return initialized async engine, creating it if necessary."""
    if _engine is None:
        return initialize_database_engine()
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Return initialized async session factory."""
    if _session_factory is None:
        initialize_database_engine()

    if _session_factory is None:
        raise RuntimeError("Failed to initialize database session factory.")

    return _session_factory


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency provider for async DB sessions."""
    async with get_session_factory()() as session:
        yield session


async def close_database_engine() -> None:
    """Dispose engine and reset singletons for clean shutdown/tests."""
    global _engine, _session_factory

    if _engine is not None:
        await _engine.dispose()
    _engine = None
    _session_factory = None
