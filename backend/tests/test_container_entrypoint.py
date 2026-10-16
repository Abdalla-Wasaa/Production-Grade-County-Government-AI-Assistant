"""Container infrastructure is tested without network or actual credentials."""

import importlib.util
import secrets
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from sqlalchemy.engine import URL

SPEC = importlib.util.spec_from_file_location(
    "container_entrypoint", Path(__file__).resolve().parents[1] / "docker" / "entrypoint.py"
)
entrypoint = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(entrypoint)


def make_secret(directory, filename):
    value = URL.create(
        "postgresql+psycopg",
        username="county_runtime",
        password=secrets.token_hex(16),
        host="db",
        database="county_local",
    ).render_as_string(hide_password=False)
    (directory / filename).write_text(value)
    return value


def test_serve_only_loads_runtime_secret(tmp_path, monkeypatch):
    value = make_secret(tmp_path, "runtime_database_url")
    monkeypatch.setenv("COUNTY_MIGRATION_DATABASE_URL", "must-be-cleared")
    arguments = []
    monkeypatch.setattr(entrypoint.os, "execv", lambda *args: arguments.append(args))
    assert entrypoint.launch("serve", tmp_path) == 0
    assert entrypoint.os.environ["COUNTY_DATABASE_URL"] == value
    assert "COUNTY_MIGRATION_DATABASE_URL" not in entrypoint.os.environ
    assert value not in repr(arguments)
    assert "--no-access-log" in arguments[0][1]


@pytest.mark.parametrize("operation", ["upgrade", "check"])
def test_migration_uses_only_migration_secret(tmp_path, monkeypatch, operation):
    value = make_secret(tmp_path, "migration_database_url")
    monkeypatch.setenv("COUNTY_DATABASE_URL", "must-be-cleared")
    monkeypatch.setattr(
        entrypoint.subprocess, "run", lambda *args, **kwargs: SimpleNamespace(returncode=0)
    )
    grant = AsyncMock()
    monkeypatch.setattr(entrypoint, "grant_revision", grant)
    assert entrypoint.launch(operation, tmp_path) == 0
    assert entrypoint.os.environ["COUNTY_MIGRATION_DATABASE_URL"] == value
    assert "COUNTY_DATABASE_URL" not in entrypoint.os.environ
    assert grant.await_count == (1 if operation == "upgrade" else 0)


def test_failed_migration_cannot_grant_permissions(tmp_path, monkeypatch):
    make_secret(tmp_path, "migration_database_url")
    monkeypatch.setattr(
        entrypoint.subprocess, "run", lambda *args, **kwargs: SimpleNamespace(returncode=1)
    )
    grant = AsyncMock()
    monkeypatch.setattr(entrypoint, "grant_revision", grant)
    with pytest.raises(RuntimeError):
        entrypoint.launch("upgrade", tmp_path)
    grant.assert_not_awaited()


def test_launcher_failure_is_generic(monkeypatch, capsys):
    monkeypatch.setattr(entrypoint.sys, "argv", ["entrypoint", "serve"])

    def fail(*args):
        raise RuntimeError("sensitive-driver-error")

    monkeypatch.setattr(entrypoint, "launch", fail)
    assert entrypoint.main() == 1
    assert "sensitive-driver-error" not in capsys.readouterr().err
