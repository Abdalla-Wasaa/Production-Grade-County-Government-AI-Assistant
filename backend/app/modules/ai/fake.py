"""Deterministic synthetic replies with no transport, credentials or prompt echo."""

from app.modules.ai.contracts import (
    ErrorCode,
    GenerationRequest,
    GenerationResult,
    ProviderError,
    Usage,
)


class FakeProvider:
    def __init__(self, max_output_tokens: int = 512) -> None:
        self._limit = max_output_tokens
        self._closed = False

    async def generate(self, request: GenerationRequest) -> GenerationResult:
        if self._closed:
            raise ProviderError(ErrorCode.UNAVAILABLE)
        if request.max_output_tokens > self._limit:
            raise ProviderError(ErrorCode.INVALID_REQUEST)
        text = (
            "[Synthetic fake response]"
            if request.language == "en"
            else "[Jibu bandia la majaribio]"
        )
        return GenerationResult(
            content=text,
            provider="fake",
            model="fake-v1",
            usage=Usage(),
            finish_reason="stop",
            synthetic=True,
        )

    async def aclose(self) -> None:
        self._closed = True
