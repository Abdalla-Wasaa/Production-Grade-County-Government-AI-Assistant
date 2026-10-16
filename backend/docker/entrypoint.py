"""Container-only secret loading and explicit migration orchestration."""

import argparse
import asyncio
import os
import subprocess
import sys
from pathlib import Path

from pydantic import SecretStr
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import validate_database_url
from app.db.session import protect_engine_logging


def read_secret(path: Path) -> SecretStr:
    value = path.read_text().strip()
    if not value or len(value) > 4096:
        raise ValueError("Invalid secret file")
    secret = SecretStr(value)
    validate_database_url(secret)
    return secret


async def grant_revision(secret: SecretStr) -> None:
    engine = create_async_engine(
        secret.get_secret_value(),
        poolclass=NullPool,
        echo=False,
        hide_parameters=True,
        connect_args={"connect_timeout": 5},
    )
    protect_engine_logging(engine)
    try:
        async with asyncio.timeout(10), engine.begin() as connection:
            await connection.execute(
                text("GRANT SELECT ON TABLE public.alembic_version TO county_runtime")
            )
    finally:
        await engine.dispose()


def launch(operation: str, secret_directory: Path = Path("/run/secrets")) -> int:
    os.environ.pop("COUNTY_DATABASE_URL", None)
    os.environ.pop("COUNTY_MIGRATION_DATABASE_URL", None)
    filename = "runtime_database_url" if operation == "serve" else "migration_database_url"
    secret = read_secret(secret_directory / filename)
    if operation == "serve":
        os.environ["COUNTY_DATABASE_URL"] = secret.get_secret_value()
        os.execv(
            sys.executable,
            [
                sys.executable,
                "-m",
                "uvicorn",
                "app.main:create_app",
                "--factory",
                "--host",
                "0.0.0.0",
                "--port",
                "8000",
                "--no-access-log",
                "--no-proxy-headers",
                "--no-server-header",
                "--timeout-graceful-shutdown",
                "20",
            ],
        )
    else:
        os.environ["COUNTY_MIGRATION_DATABASE_URL"] = secret.get_secret_value()
        result = subprocess.run(
            [sys.executable, "-m", "app.db.migrate", operation],
            capture_output=True,
            timeout=75,
            check=False,
        )
        if result.returncode:
            raise RuntimeError("Migration failed")
        if operation == "upgrade":
            asyncio.run(grant_revision(secret))
        print("Database migration operation completed.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Container process launcher")
    parser.add_argument("operation", choices=["serve", "upgrade", "check"])
    operation = parser.parse_args().operation
    try:
        return launch(operation)
    except Exception:
        print(
            "Container operation failed; review local configuration and dependency state.",
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
