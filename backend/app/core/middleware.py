"""ASGI boundaries keep request IDs on every HTTP response, including CORS/errors."""

import logging
from time import monotonic
from uuid import uuid4

from starlette.datastructures import Headers, MutableHeaders
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core.errors import error_response


class LocalCORSMiddleware(CORSMiddleware):
    """Keep Starlette's CORS policy but normalize rejected preflight responses."""

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "http" and scope["method"] == "OPTIONS":
            headers = Headers(scope=scope)
            if "origin" in headers and "access-control-request-method" in headers:
                response = self.preflight_response(request_headers=headers)
                if response.status_code == 400:
                    error = error_response(Request(scope), 400, "cors_rejected")
                    for name, value in response.headers.items():
                        if name.startswith("access-control-") or name == "vary":
                            error.headers[name] = value
                    await error(scope, receive, send)
                    return
        await super().__call__(scope, receive, send)


class ErrorBoundaryMiddleware:
    def __init__(self, app: ASGIApp, logger: logging.Logger) -> None:
        self.app = app
        self.logger = logger

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        started = False

        async def track_send(message: Message) -> None:
            nonlocal started
            if message["type"] == "http.response.start":
                started = True
            await send(message)

        try:
            await self.app(scope, receive, track_send)
        except Exception:
            self.logger.error("request_failed", extra={"request_id": scope["state"]["request_id"]})
            # Once headers are sent a response cannot be replaced. Streaming is
            # outside P1-01; never emit exception content or a second response.
            if not started:
                await error_response(Request(scope), 500, "internal_error")(scope, receive, send)


class RequestContextMiddleware:
    def __init__(self, app: ASGIApp, logger: logging.Logger) -> None:
        self.app = app
        self.logger = logger

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        request_id = str(uuid4())
        scope.setdefault("state", {})["request_id"] = request_id
        started_at = monotonic()
        status = 500

        async def response_send(message: Message) -> None:
            nonlocal status
            if message["type"] == "http.response.start":
                status = message["status"]
                headers = MutableHeaders(scope=message)
                headers["X-Request-ID"] = request_id
                headers["Cache-Control"] = "no-store"
            await send(message)

        try:
            await self.app(scope, receive, response_send)
        finally:
            self.logger.info(
                "request_completed",
                extra={
                    "request_id": request_id,
                    "method": scope["method"],
                    "status_code": status,
                    "duration_ms": (monotonic() - started_at) * 1000,
                },
            )
