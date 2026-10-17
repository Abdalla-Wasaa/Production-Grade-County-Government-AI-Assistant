"""Enforce the auth body cap before JSON parsing, including chunked requests."""

from starlette.requests import Request
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core.errors import error_response


class AuthBodyLimit:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or not scope["path"].startswith("/api/v1/auth/"):
            await self.app(scope, receive, send)
            return
        messages: list[Message] = []
        size = 0
        while True:
            message = await receive()
            size += len(message.get("body", b""))
            if size > 32768:
                await error_response(Request(scope), 413, "request_too_large")(scope, receive, send)
                return
            messages.append(message)
            if message["type"] == "http.disconnect" or not message.get("more_body", False):
                break
        index = 0

        async def replay() -> Message:
            nonlocal index
            if index < len(messages):
                message = messages[index]
                index += 1
                return message
            return await receive()

        await self.app(scope, replay, send)
