"""Network-free configuration, readiness and resource ownership checks."""

import asyncio
import logging
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr, ValidationError

from app.core.config import ConfigurationError, Settings, load_settings
from app.db.base import Base
from app.db.readiness import is_ready
from app.db.session import Database
from app.main import create_app
from app.modules.conversations import models as conversation_models  # noqa: F401
from app.modules.identity import models  # noqa: F401 -- reviewed metadata
from app.modules.privacy import models as privacy_models  # noqa: F401 -- reviewed metadata


@pytest.mark.parametrize(
    "url",
    [
        "",
        "secret",
        "sqlite:///test",
        "postgresql://u:p@host/db",
        "postgresql+psycopg://u:p@host/db?options=secret",
        "postgresql+psycopg://u:p@host:99999/db",
    ],
)
def test_invalid_url_is_safe(url, monkeypatch):
    monkeypatch.setenv("COUNTY_ENVIRONMENT", "test")
    monkeypatch.setenv("COUNTY_DATABASE_URL", url)
    with pytest.raises(ConfigurationError) as error:
        load_settings()
    assert url not in str(error.value) if url else True
    assert "secret" not in str(error.value)


@pytest.mark.parametrize(
    "field,value",
    [
        ("db_pool_size", 0),
        ("db_max_overflow", -1),
        ("db_connect_timeout_seconds", 1),
        ("db_pool_timeout_seconds", 0),
        ("db_readiness_timeout_seconds", 0),
    ],
)
def test_invalid_pool_configuration(field, value):
    with pytest.raises(ValidationError):
        Settings(environment="test", **{field: value})


def test_valid_settings_hide_secret():
    config = Settings(
        environment="test",
        database_url=SecretStr("postgresql+psycopg://runtime:synthetic-password@localhost/test"),
    )
    assert "synthetic-password" not in repr(config)
    assert "synthetic-password" not in config.model_dump_json()
    assert config.db_pool_size == config.db_max_overflow == 5
    assert config.db_readiness_timeout_seconds == 10
    assert set(Base.metadata.tables) == {
        "conversations",
        "messages",
        "users",
        "invitations",
        "auth_sessions",
        "refresh_tokens",
        "auth_audit_events",
        "auth_rate_limits",
        "privacy_operators",
        "privacy_holds",
        "privacy_deletion_requests",
        "privacy_deletion_ledger",
        "privacy_maintenance_state",
    }


def test_missing_database_ready_503_bilingual(client):
    for language in ["en", "sw"]:
        response = client.get("/health/ready", headers={"Accept-Language": language})
        assert response.status_code == 503
        assert response.json()["error"]["code"] == "service_unavailable"
        assert response.json()["error"]["request_id"] == response.headers["X-Request-ID"]
        assert response.headers["Cache-Control"] == "no-store"
        assert response.json()["error"]["details"] == []
    assert client.get("/health/live").status_code == 200


async def test_complete_readiness_deadline():
    class SlowConnection:
        async def __aenter__(self):
            await asyncio.sleep(2)

        async def __aexit__(self, *args):
            pass

    database = Database(Settings(environment="test"))

    class Engine:
        def connect(self):
            return SlowConnection()

    database.engine = Engine()
    start = asyncio.get_running_loop().time()
    assert not await is_ready(database, 0.02)
    assert asyncio.get_running_loop().time() - start < 0.5


def test_engine_disposed_on_exception(monkeypatch):
    dispose = AsyncMock()
    monkeypatch.setattr(Database, "dispose", dispose)
    with pytest.raises(RuntimeError), TestClient(create_app(Settings(environment="test"))):
        raise RuntimeError("synthetic failure")
    dispose.assert_awaited_once()


def test_configured_startup_remains_lazy_without_network():
    config = Settings(
        environment="test",
        database_url=SecretStr("postgresql+psycopg://runtime:synthetic@localhost:5432/unused"),
    )
    with TestClient(create_app(config)) as client:
        assert client.get("/health/live").status_code == 200
        assert client.app.state.database.engine.pool.checkedout() == 0


def test_runtime_does_not_hold_migration_secret(monkeypatch):
    monkeypatch.setenv("COUNTY_MIGRATION_DATABASE_URL", "secret-not-for-runtime")
    config = Settings(environment="test")
    assert "secret-not-for-runtime" not in config.model_dump_json()
    assert not hasattr(config, "migration_database_url")


def test_engine_pool_diagnostics_do_not_expose_secrets(capsys):
    app = create_app(
        Settings(
            environment="test",
            database_url=SecretStr("postgresql+psycopg://runtime:synthetic@localhost/unused"),
        )
    )
    with TestClient(app):
        engine = app.state.database.engine
        assert not engine.sync_engine.logger.isEnabledFor(logging.INFO)
        assert not engine.sync_engine.pool.logger.isEnabledFor(logging.DEBUG)
        engine.sync_engine.logger.error("postgresql://private:password@internal-host/db")
        engine.sync_engine.pool.logger.error("connection password=private", exc_info=True)
    output = capsys.readouterr().err
    assert "internal-host" not in output
    assert "password" not in output
    assert '"event": "redacted"' in output


def test_logging_cleanup_even_if_disposal_fails(monkeypatch):
    app = create_app(Settings(environment="test"))
    monkeypatch.setattr(Database, "dispose", AsyncMock(side_effect=RuntimeError("cleanup failed")))
    with pytest.raises(RuntimeError, match="cleanup failed"), TestClient(app):
        pass
    assert not app.state.started
    assert app.state.logger.handlers == []
