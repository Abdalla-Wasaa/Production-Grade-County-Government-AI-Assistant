"""Uncached readiness with a complete-operation deadline."""

import asyncio

from alembic.script import ScriptDirectory
from sqlalchemy import Connection, text

from app.db.migrate import migration_config
from app.db.session import Database


def revision_matches(connection: Connection) -> bool:
    expected = tuple(ScriptDirectory.from_config(migration_config()).get_heads())
    # Explicit schema prevents search_path substitution; bound unexpected row counts.
    actual = tuple(
        connection.execute(text("SELECT version_num FROM public.alembic_version LIMIT 2")).scalars()
    )
    return len(expected) == 1 and actual == expected


async def is_ready(database: Database, timeout: float) -> bool:
    if database.engine is None:
        return False
    try:
        # Pool checkout, pre-ping, queries and connection return share one deadline.
        async with asyncio.timeout(timeout), database.engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
            return await connection.run_sync(revision_matches)
    except Exception:
        return False
