"""Implemented-provider registry, bounded execution and lifecycle ownership."""

import asyncio
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager

from app.core.config import ConfigurationError
from app.modules.ai.contracts import (
    AIProvider,
    ErrorCode,
    GenerationRequest,
    GenerationResult,
    ModelIdentity,
    ProviderError,
)
from app.modules.ai.fake import FakeProvider
from app.modules.ai.ollama import OllamaProvider
from app.modules.ai.settings import AISettings


class ManagedProvider:
    """A deadline includes admission waiting. Caller cancellation always propagates."""

    def __init__(self, provider: AIProvider, settings: AISettings) -> None:
        self._provider = provider
        self._settings = settings
        self._identity = ModelIdentity(provider=settings.provider, model=settings.model)
        self._slots = asyncio.Semaphore(settings.max_concurrency)
        self._closed = False

    async def generate(self, request: GenerationRequest) -> GenerationResult:
        if self._closed:
            raise ProviderError(ErrorCode.UNAVAILABLE)
        if request.max_output_tokens > self._settings.max_output_tokens:
            raise ProviderError(ErrorCode.INVALID_REQUEST)
        try:
            async with asyncio.timeout(self._settings.timeout_seconds), self._slots:
                result = await self._provider.generate(request)
            if result.identity != self._identity:
                raise ProviderError(ErrorCode.INVALID_RESPONSE)
            return result
        except TimeoutError:
            raise ProviderError(ErrorCode.TIMEOUT) from None
        except ProviderError:
            raise
        except Exception:
            # Never retain/log provider exception text, prompt content or credentials.
            raise ProviderError(ErrorCode.UNAVAILABLE) from None

    async def aclose(self) -> None:
        self._closed = True
        await self._provider.aclose()


def _fake(_: AISettings) -> AIProvider:
    return FakeProvider()


_BUILDERS: dict[str, Callable[[AISettings], AIProvider]] = {
    "fake": _fake,
    "ollama": OllamaProvider,
}


@asynccontextmanager
async def provider_context(settings: AISettings) -> AsyncIterator[AIProvider]:
    builder = _BUILDERS.get(settings.provider)
    if builder is None:
        raise ConfigurationError("Unsupported AI provider")
    provider = ManagedProvider(builder(settings), settings)
    try:
        yield provider
    finally:
        await provider.aclose()
