"""Async privileged migration runner; no credential-bearing INI or logging."""

import asyncio

from alembic import context
from sqlalchemy import Connection
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool

from app.db.base import Base
from app.db.migrate import MigrationSettings
from app.db.session import protect_engine_logging
from app.modules.conversations import models as conversation_models  # noqa: F401
from app.modules.identity import models  # noqa: F401 -- register reviewed model metadata
from app.modules.privacy import models as privacy_models  # noqa: F401


def run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection, target_metadata=Base.metadata, version_table_schema="public"
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_online() -> None:
    secret = context.config.attributes.get("database_url")
    if secret is None:
        secret = MigrationSettings().migration_database_url
    engine = create_async_engine(
        secret.get_secret_value(),
        poolclass=NullPool,
        hide_parameters=True,
        echo=False,
        connect_args={"connect_timeout": 5},
    )
    protect_engine_logging(engine)
    try:
        async with asyncio.timeout(60), engine.connect() as connection:
            await connection.run_sync(run_migrations)
    finally:
        await engine.dispose()


if context.is_offline_mode():
    raise RuntimeError("Offline migrations are not supported")
asyncio.run(run_online())
