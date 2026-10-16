"""Tests are environment-independent and forbid external network connections."""

import os
import socket
from collections.abc import Iterator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app


@pytest.fixture(autouse=True)
def isolated_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in os.environ:
        if name.startswith("COUNTY_"):
            monkeypatch.delenv(name)

    def deny_network(*args: object, **kwargs: object) -> None:
        raise AssertionError("Foundation tests must not contact external services")

    monkeypatch.setattr(socket, "create_connection", deny_network)
    monkeypatch.setattr(socket.socket, "connect", deny_network)


@pytest.fixture
def app() -> FastAPI:
    return create_app(Settings(environment="test"))


@pytest.fixture
def client(app: FastAPI) -> Iterator[TestClient]:
    with TestClient(app) as value:
        yield value
