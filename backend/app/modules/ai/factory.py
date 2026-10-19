"""Provider registry and resource ownership; construction performs no network I/O."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx

from app.modules.ai.contracts import AIProvider
from app.modules.ai.fake import FakeProvider
from app.modules.ai.ollama import OllamaProvider
from app.modules.ai.settings import AISettings


@asynccontextmanager
async def provider_context(
    settings: AISettings, *, transport: httpx.AsyncBaseTransport | None = None
) -> AsyncIterator[AIProvider]:
    provider: AIProvider
    if settings.provider == "fake":
        provider = FakeProvider(settings.max_output_tokens)
    else:
        provider = OllamaProvider(settings, transport=transport)
    try:
        yield provider
    finally:
        await provider.aclose()
