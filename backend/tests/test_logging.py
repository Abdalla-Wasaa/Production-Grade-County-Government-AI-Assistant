"""Privacy-aware logging omits unknown payloads and validates safe metadata."""

import json
import logging
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.logging import SafeJSONFormatter


def test_formatter_drops_sensitive_text_extras_and_tracebacks() -> None:
    sentinel = "private-input-sentinel"
    record = logging.LogRecord("test", logging.ERROR, __file__, 1, sentinel, (), None)
    record.password = sentinel
    record.authorization = f"Bearer {sentinel}"
    record.settings = {"secret": sentinel}
    record.request_id = sentinel
    record.method = sentinel
    record.status_code = sentinel
    record.duration_ms = float("nan")
    try:
        raise RuntimeError(sentinel)
    except RuntimeError as exc:
        record.exc_info = (type(exc), exc, exc.__traceback__)
    rendered = SafeJSONFormatter().format(record)
    assert sentinel not in rendered
    assert set(json.loads(rendered)) == {"timestamp", "level", "event"}
    assert json.loads(rendered)["event"] == "redacted"


def test_formatter_keeps_safe_operational_metadata() -> None:
    record = logging.LogRecord("test", logging.INFO, __file__, 1, "request_completed", (), None)
    record.request_id = str(uuid4())
    record.method = "GET"
    record.status_code = 200
    record.duration_ms = 1.23456
    data = json.loads(SafeJSONFormatter().format(record))
    assert data["request_id"] == record.request_id
    assert data["duration_ms"] == 1.235
    assert data["status_code"] == 200


@pytest.mark.parametrize(
    "elapsed", [float("nan"), float("inf"), -1, 10**1000, "private-input-sentinel"]
)
def test_formatter_rejects_unbounded_or_invalid_timing(elapsed: object) -> None:
    record = logging.LogRecord("test", logging.INFO, __file__, 1, "request_completed", (), None)
    record.duration_ms = elapsed
    assert "duration_ms" not in json.loads(SafeJSONFormatter().format(record))


def test_request_logs_never_include_urls_headers_or_bodies(
    app: FastAPI, capsys: pytest.CaptureFixture[str]
) -> None:
    sentinel = "private-input-sentinel"
    with TestClient(app) as client:
        response = client.get(
            f"/{sentinel}?password={sentinel}",
            headers={"Authorization": f"Bearer {sentinel}", "Cookie": f"session={sentinel}"},
        )
    output = capsys.readouterr().err
    assert sentinel not in output
    rows = [json.loads(line) for line in output.splitlines()]
    request = next(row for row in rows if row["event"] == "request_completed")
    assert request["request_id"] == response.headers["x-request-id"]
    assert request["status_code"] == 404
