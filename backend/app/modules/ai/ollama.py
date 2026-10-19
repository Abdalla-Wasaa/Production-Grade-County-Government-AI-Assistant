"""Bounded Ollama /api/chat adapter. No retries, downloads, redirects or cloud fallback."""

import asyncio
import json
from typing import Literal

import httpx
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app.modules.ai.contracts import (
    ErrorCode,
    GenerationRequest,
    GenerationResult,
    ProviderError,
    Usage,
)
from app.modules.ai.settings import AISettings


class _ReplyMessage(BaseModel):
    model_config = ConfigDict(strict=True, extra="ignore", hide_input_in_errors=True)
    role: Literal["assistant"]
    content: str = Field(min_length=1, max_length=16000, repr=False)
    tool_calls: list[object] = Field(default_factory=list, max_length=0)


class _Reply(BaseModel):
    model_config = ConfigDict(strict=True, extra="ignore", hide_input_in_errors=True)
    model: str
    message: _ReplyMessage
    done: bool
    done_reason: Literal["stop", "length"]
    prompt_eval_count: int = Field(ge=0)
    eval_count: int = Field(ge=0)


class OllamaProvider:
    def __init__(self, settings: AISettings, *, transport: httpx.AsyncBaseTransport | None = None):
        self._settings = settings
        self._model = str(settings.model)
        headers = {"Accept": "application/json", "Accept-Encoding": "identity"}
        if settings.ollama_api_key is not None:
            headers["Authorization"] = "Bearer " + settings.ollama_api_key.get_secret_value()
        self._client = httpx.AsyncClient(
            base_url=settings.ollama_base_url,
            headers=headers,
            transport=transport,
            trust_env=False,
            follow_redirects=False,
            timeout=httpx.Timeout(settings.timeout_seconds, connect=5),
            limits=httpx.Limits(
                max_connections=settings.max_concurrency, max_keepalive_connections=1
            ),
        )
        self._slots = asyncio.Semaphore(settings.max_concurrency)
        self._closed = False

    async def generate(self, request: GenerationRequest) -> GenerationResult:
        if self._closed:
            raise ProviderError(ErrorCode.UNAVAILABLE)
        if request.max_output_tokens > self._settings.max_output_tokens:
            raise ProviderError(ErrorCode.INVALID_REQUEST)
        payload = {
            "model": self._model,
            "messages": [message.model_dump() for message in request.messages],
            "stream": False,
            "options": {"num_predict": request.max_output_tokens, "num_ctx": 8192},
        }
        # Deadline includes admission waiting, connection, generation and bounded body read.
        try:
            async with (
                asyncio.timeout(self._settings.timeout_seconds),
                self._slots,
                self._client.stream("POST", "/api/chat", json=payload) as response,
            ):
                if response.status_code != 200:
                    codes = {404: ErrorCode.MODEL_NOT_FOUND, 429: ErrorCode.RATE_LIMITED}
                    code = codes.get(response.status_code)
                    if code is None:
                        code = (
                            ErrorCode.UNAVAILABLE
                            if response.status_code >= 500
                            else ErrorCode.REJECTED
                        )
                    raise ProviderError(code)
                if response.headers.get("content-type", "").split(";", 1)[0] != "application/json":
                    raise ProviderError(ErrorCode.INVALID_RESPONSE)
                if response.headers.get("content-encoding", "identity") != "identity":
                    raise ProviderError(ErrorCode.INVALID_RESPONSE)
                body = bytearray()
                async for chunk in response.aiter_bytes(chunk_size=8192):
                    if len(body) + len(chunk) > self._settings.max_response_bytes:
                        raise ProviderError(ErrorCode.INVALID_RESPONSE)
                    body.extend(chunk)
            reply = _Reply.model_validate(json.loads(body))
            if (
                not reply.done
                or reply.model != self._model
                or not reply.message.content.strip()
                or reply.eval_count > request.max_output_tokens
            ):
                raise ProviderError(ErrorCode.INVALID_RESPONSE)
            return GenerationResult(
                content=reply.message.content,
                provider="ollama",
                model=reply.model,
                usage=Usage(input_tokens=reply.prompt_eval_count, output_tokens=reply.eval_count),
                finish_reason=reply.done_reason,
                synthetic=False,
            )
        except (TimeoutError, httpx.TimeoutException):
            raise ProviderError(ErrorCode.TIMEOUT) from None
        except httpx.HTTPError:
            raise ProviderError(ErrorCode.UNAVAILABLE) from None
        except (ValueError, ValidationError):
            raise ProviderError(ErrorCode.INVALID_RESPONSE) from None

    async def aclose(self) -> None:
        self._closed = True
        await self._client.aclose()
