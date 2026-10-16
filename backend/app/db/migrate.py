"""Explicit credential-safe commands; never invoked by HTTP or startup."""

import argparse
import asyncio
import sys
from importlib.resources import files

from alembic import command
from alembic.config import Config
from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import validate_database_url
from app.db.session import protect_engine_logging


class MigrationSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="COUNTY_", env_file=None, hide_input_in_errors=True
    )
    migration_database_url: SecretStr

    @field_validator("migration_database_url")
    @classmethod
    def validate_url(cls, value: SecretStr) -> SecretStr:
        validate_database_url(value)
        return value


def migration_config() -> Config:
    config = Config()
    config.set_main_option("script_location", str(files("migrations")))
    return config


async def check_revision(secret: SecretStr) -> None:
    from app.db.readiness import revision_matches

    engine = create_async_engine(
        secret.get_secret_value(),
        poolclass=NullPool,
        hide_parameters=True,
        connect_args={"connect_timeout": 5},
    )
    protect_engine_logging(engine)
    try:
        async with asyncio.timeout(10), engine.connect() as connection:
            if not await connection.run_sync(revision_matches):
                raise RuntimeError("Schema is not current")
    finally:
        await engine.dispose()


def main() -> int:
    parser = argparse.ArgumentParser(description="Explicit PostgreSQL migrations")
    parser.add_argument("operation", choices=["upgrade", "check"])
    operation = parser.parse_args().operation
    try:
        settings = MigrationSettings()
        config = migration_config()
        config.attributes["database_url"] = settings.migration_database_url
        if operation == "upgrade":
            command.upgrade(config, "head")
        else:
            asyncio.run(check_revision(settings.migration_database_url))
    except Exception:
        print(
            "Database migration operation failed; review configuration and database state.",
            file=sys.stderr,
        )
        return 1
    print("Database migration operation completed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
