"""Real request failures have safe envelopes, correlation headers and CORS."""

from typing import Annotated
from uuid import UUID

import pytest
from fastapi import Depends, FastAPI, HTTPException
from fastapi.testclient import TestClient
from pydantic import BaseModel, ConfigDict

from app.core.config import Settings
from app.main import create_app

SENTINEL = "private-input-sentinel"


class Payload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    count: int


def test_errors_hide_input_and_exception_details(
    app: FastAPI, capsys: pytest.CaptureFixture[str]
) -> None:
    # Test-only routes exercise boundary handlers without adding product features.
    @app.post("/test-validation")
    async def validate(payload: Payload) -> dict[str, int]:
        return {"count": payload.count}

    @app.get("/test-http")
    async def http_error() -> None:
        raise HTTPException(400, detail=SENTINEL)

    def fail() -> None:
        raise RuntimeError(SENTINEL)

    @app.get("/test-exception")
    async def exception(_dependency: Annotated[None, Depends(fail)]) -> None:
        pass

    with TestClient(app) as client:
        responses = [
            client.get(f"/{SENTINEL}?password={SENTINEL}"),
            client.post("/health/live"),
            client.post("/test-validation", json={"count": SENTINEL, SENTINEL: SENTINEL}),
            client.get("/test-http"),
            client.get("/test-exception", headers={"Authorization": f"Bearer {SENTINEL}"}),
        ]
    assert [r.status_code for r in responses] == [404, 405, 422, 400, 500]
    assert responses[1].headers["allow"] == "GET"
    for response in responses:
        error = response.json()["error"]
        assert set(error) == {"code", "message", "request_id", "details"}
        assert error["request_id"] == response.headers["x-request-id"]
        UUID(error["request_id"])
        assert SENTINEL not in response.text
        assert response.headers["cache-control"] == "no-store"
    assert responses[2].json()["error"]["details"] == [{"field": "request", "code": "invalid"}]
    assert SENTINEL not in capsys.readouterr().err


def test_kiswahili_error(client: TestClient) -> None:
    response = client.get("/missing", headers={"Accept-Language": "sw"})
    assert response.json()["error"]["message"] == "Rasilimali haikupatikana."


def test_cors_disabled_by_default(client: TestClient) -> None:
    response = client.get("/health/live", headers={"Origin": "http://localhost:5173"})
    assert "access-control-allow-origin" not in response.headers


def test_explicit_local_cors_and_error_behavior() -> None:
    origin = "http://localhost:5173"
    app = create_app(Settings(environment="test", cors_origins=(origin,)))

    @app.get("/test-exception")
    async def fail() -> None:
        raise RuntimeError(SENTINEL)

    with TestClient(app) as client:
        for path, status in [("/health/live", 200), ("/missing", 404), ("/test-exception", 500)]:
            response = client.get(path, headers={"Origin": origin})
            assert response.status_code == status
            assert response.headers["access-control-allow-origin"] == origin
            assert "access-control-allow-credentials" not in response.headers
        allowed = client.options(
            "/health/live",
            headers={"Origin": origin, "Access-Control-Request-Method": "GET"},
        )
        assert allowed.status_code == 200
        assert "x-request-id" in allowed.headers
        for candidate, method in [("https://hostile.example.invalid", "GET"), (origin, "POST")]:
            denied = client.options(
                "/health/live",
                headers={"Origin": candidate, "Access-Control-Request-Method": method},
            )
            assert denied.status_code == 400
            assert denied.json()["error"]["code"] == "cors_rejected"
            assert denied.json()["error"]["request_id"] == denied.headers["x-request-id"]
        hostile = client.get("/health/live", headers={"Origin": "https://hostile.example.invalid"})
        assert "access-control-allow-origin" not in hostile.headers
