"""Structured application logs with data minimization and redaction by omission."""

import json
import logging
from contextlib import suppress
from datetime import UTC, datetime
from uuid import UUID

EVENTS = {"application_started", "application_stopped", "request_completed", "request_failed"}
METHODS = {"GET", "HEAD", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"}


class SafeJSONFormatter(logging.Formatter):
    """Unknown messages/extras and all exception bodies are deliberately discarded.

    Regexes cannot redact arbitrary credentials reliably. Only bounded, typed
    operational fields are released, including when a caller logs sensitive text.
    """

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, object] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "event": record.msg
            if isinstance(record.msg, str) and record.msg in EVENTS
            else "redacted",
        }
        request_id = getattr(record, "request_id", None)
        if isinstance(request_id, str) and len(request_id) == 36:
            with suppress(ValueError):
                payload["request_id"] = str(UUID(request_id))
        method = getattr(record, "method", None)
        if isinstance(method, str) and method in METHODS:
            payload["method"] = method
        status = getattr(record, "status_code", None)
        if type(status) is int and 100 <= status <= 599:
            payload["status_code"] = status
        elapsed = getattr(record, "duration_ms", None)
        if type(elapsed) in (int, float) and 0 <= elapsed <= 86_400_000:
            payload["duration_ms"] = round(elapsed, 3)
        return json.dumps(payload, allow_nan=False)


def make_logger(level: str) -> logging.Logger:
    """Return a per-application logger without changing global or server logging."""
    logger = logging.Logger("county_backend", level=level)
    logger.propagate = False
    return logger
