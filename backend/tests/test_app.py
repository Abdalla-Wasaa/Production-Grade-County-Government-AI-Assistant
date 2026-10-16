"""App factory, lifecycle and dependency-free liveness contracts."""

import json
import os
import subprocess
import sys
from uuid import UUID

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app


def test_factory_isolated_and_no_logging_until_startup(app: FastAPI) -> None:
    other = create_app(Settings(environment="test"))
    assert app is not other
    assert app.state.logger is not other.state.logger
    assert app.state.started is False
    assert app.state.logger.handlers == []


def test_lifecycle_cleans_up_after_exception(
    app: FastAPI, capsys: pytest.CaptureFixture[str]
) -> None:
    with pytest.raises(RuntimeError, match="test failure"), TestClient(app):
        assert app.state.started is True
        assert len(app.state.logger.handlers) == 1
        raise RuntimeError("test failure")
    assert app.state.started is False
    assert app.state.logger.handlers == []
    events = [json.loads(line)["event"] for line in capsys.readouterr().err.splitlines()]
    assert events == ["application_started", "application_stopped"]
    with TestClient(app):
        assert len(app.state.logger.handlers) == 1
    assert app.state.logger.handlers == []


def test_liveness_without_external_dependencies(client: TestClient) -> None:
    response = client.get("/health/live", headers={"X-Request-ID": "untrusted-id"})
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert str(UUID(response.headers["X-Request-ID"])) == response.headers["X-Request-ID"]
    assert response.headers["Cache-Control"] == "no-store"
    assert response.headers["X-Request-ID"] != client.get("/health/live").headers["X-Request-ID"]


@pytest.mark.parametrize("path", ["/api/v1/auth/login", "/api/v1/conversations", "/docs"])
def test_future_endpoints_absent(client: TestClient, path: str) -> None:
    assert client.get(path).status_code == 404


def test_openapi_only_exposes_operational_health(client: TestClient) -> None:
    schema = client.get("/api/v1/openapi.json").json()
    assert set(schema["paths"]) == {"/health/live", "/health/ready"}
    assert schema["info"]["version"] == "0.1.0"


def test_import_does_not_create_app_or_change_root_logger() -> None:
    environment = {k: v for k, v in os.environ.items() if not k.startswith("COUNTY_")}
    code = """
import logging, socket
before = list(logging.getLogger().handlers)
def deny(*args, **kwargs):
    raise AssertionError('network during import')
socket.socket.connect = deny
import app.main
assert not hasattr(app.main, 'app')
assert before == list(logging.getLogger().handlers)
"""
    result = subprocess.run(
        [sys.executable, "-c", code], env=environment, capture_output=True, text=True
    )
    assert result.returncode == 0, result.stderr
