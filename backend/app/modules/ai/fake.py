"""Deterministic synthetic replies; no network transport, credentials or prompt echo."""

import asyncio
import math

from app.modules.ai.contracts import (
    ErrorCode,
    GenerationRequest,
    GenerationResult,
    ModelIdentity,
    ProviderError,
    Usage,
)


class FakeProvider:
    def __init__(self, *, delay_seconds: float = 0, failure: ErrorCode | None = None) -> None:
        # Fault injection is explicit Python configuration for tests, never user input or env.
        if not math.isfinite(delay_seconds) or not 0 <= delay_seconds <= 120:
            raise ValueError("Invalid synthetic delay")
        self._delay = delay_seconds
        self._failure = failure
        self._closed = False

    async def generate(self, request: GenerationRequest) -> GenerationResult:
        if self._closed:
            raise ProviderError(ErrorCode.UNAVAILABLE)
        await asyncio.sleep(self._delay)
        if self._failure is not None:
            raise ProviderError(self._failure)
        text = (
            "[Synthetic fake response]"
            if request.language == "en"
            else "[Jibu bandia la majaribio]"
        )
        return GenerationResult(
            content=text,
            identity=ModelIdentity(provider="fake", model="fake-v1"),
            usage=Usage(),
            finish_reason="stop",
            synthetic=True,
        )

    async def aclose(self) -> None:
        self._closed = True
