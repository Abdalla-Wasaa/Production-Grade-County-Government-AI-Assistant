"""Lazy per-app resources and explicit transaction ownership."""

import logging
from collections.abc import AsyncIterator

import anyio
from fastapi import Request
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import Settings


class Database:
    def __init__(self, settings: Settings, logger: logging.Logger | None = None) -> None:
        self.engine: AsyncEngine | None = None
        self.sessions: async_sessionmaker[AsyncSession] | None = None
        if settings.database_url is not None:
            self.engine = create_async_engine(
                settings.database_url.get_secret_value(),
                pool_pre_ping=True,
                pool_size=settings.db_pool_size,
                max_overflow=settings.db_max_overflow,
                pool_timeout=settings.db_pool_timeout_seconds,
                connect_args={"connect_timeout": settings.db_connect_timeout_seconds},
                echo=False,
                hide_parameters=True,
            )
            protect_engine_logging(self.engine, logger)
            self.sessions = async_sessionmaker(self.engine, expire_on_commit=False)

    async def dispose(self) -> None:
        if self.engine is not None:
            with anyio.CancelScope(shield=True):
                await self.engine.dispose()


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    """One session per request/task; service code explicitly commits when intended."""
    database: Database = request.app.state.database
    if database.sessions is None:
        raise RuntimeError("Database unavailable")
    session = database.sessions()
    try:
        yield session
    finally:
        # Closing rolls back uncommitted transactions, including after cancellation.
        with anyio.CancelScope(shield=True):
            await session.close()


def protect_engine_logging(engine: AsyncEngine, logger: logging.Logger | None = None) -> None:
    """Route engine/pool diagnostics through the safe app boundary, never root logs."""
    if logger is None:
        logger = logging.Logger("county_database")
        logger.propagate = False
        logger.addHandler(logging.NullHandler())
    engine.sync_engine.logger = logger
    engine.sync_engine.pool.logger = logger
