"""Bounded, stateless orchestration over the existing provider port; no domain writes."""

import asyncio
from time import perf_counter
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.modules.ai.contracts import (
    AIProvider,
    Contract,
    ErrorCode,
    GenerationRequest,
    GenerationResult,
    Message,
    ModelIdentity,
    ProviderError,
    Usage,
)
from app.modules.ai.prompts import ABSTENTIONS, POLICY_VERSION, PROMPT_VERSION, SYSTEM_PROMPTS


class PromptSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="PROMPT_", env_file=None, extra="forbid", frozen=True, hide_input_in_errors=True
    )
    # Server-owned routing, never inferred from words or client/provider claims.
    response_policy: Literal["unverified_county", "general_information"] = "unverified_county"
    # Outer deadline includes provider admission. A shorter provider deadline still wins.
    timeout_seconds: float = Field(default=30, gt=0, le=30)
    max_output_tokens: int = Field(default=256, ge=1, le=1024)
    max_output_characters: int = Field(default=1200, ge=128, le=4000)


class PromptInput(Contract):
    content: str = Field(min_length=1, max_length=4000, repr=False)
    language: Literal["en", "sw"] = "en"

    @field_validator("content")
    @classmethod
    def nonblank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Message must contain text")
        return value


class PromptResult(Contract):
    generation: GenerationResult = Field(repr=False)
    prompt_version: str
    status: Literal["complete", "abstained", "truncated", "suspected_incomplete"]

    @property
    def displayable_content(self) -> str | None:
        # Completion is not factual approval. Raw partial text is private review data.
        return self.generation.content if self.status in {"complete", "abstained"} else None

    elapsed_seconds: float = Field(ge=0)


class PromptOrchestrator:
    """Borrow a lifecycle-managed provider. Caller owns closure; never retry implicitly.

    No client-supplied system role/history/context is accepted. Adding owned history or
    verified evidence requires a separate contract. Output remains untrusted plain text.
    """

    def __init__(self, provider: AIProvider, settings: PromptSettings) -> None:
        self._provider = provider
        self._settings = settings

    @property
    def response_policy(self) -> Literal["unverified_county", "general_information"]:
        return self._settings.response_policy

    async def generate(self, value: PromptInput) -> PromptResult:
        started = perf_counter()
        settings = self._settings
        if settings.response_policy == "unverified_county":
            content = ABSTENTIONS[value.language]
            if len(content) > settings.max_output_characters:
                raise ProviderError(ErrorCode.INVALID_REQUEST)
            return PromptResult(
                generation=GenerationResult(
                    content=content,
                    identity=ModelIdentity(provider="policy", model=POLICY_VERSION),
                    usage=Usage(),
                    finish_reason="stop",
                    synthetic=True,
                ),
                prompt_version=PROMPT_VERSION,
                status="abstained",
                elapsed_seconds=perf_counter() - started,
            )
        request = GenerationRequest(
            messages=(
                Message(
                    role="system",
                    content=(
                        SYSTEM_PROMPTS[value.language]
                        + f"\nMaximum response length: {settings.max_output_characters} Unicode "
                        "characters, including whitespace."
                    ),
                ),
                Message(role="user", content=value.content),
            ),
            language=value.language,
            max_output_tokens=settings.max_output_tokens,
        )
        try:
            async with asyncio.timeout(settings.timeout_seconds):
                result = await self._provider.generate(request)
            if len(result.content) > settings.max_output_characters:
                # Reject rather than truncate a disclaimer or return an unbounded response.
                raise ProviderError(ErrorCode.INVALID_RESPONSE)
            if (
                result.usage.output_tokens is not None
                and result.usage.output_tokens > settings.max_output_tokens
            ):
                raise ProviderError(ErrorCode.INVALID_RESPONSE)
        except TimeoutError:
            raise ProviderError(ErrorCode.TIMEOUT) from None
        except ProviderError:
            raise
        except Exception:
            raise ProviderError(ErrorCode.UNAVAILABLE) from None
        # Terminal punctuation is only a conservative completeness signal, not grammar
        # or factual verification. Never repair, silently truncate or retry content.
        terminal = result.content.rstrip().rstrip("\"'”’)]}»").rstrip()
        status: Literal["complete", "abstained", "truncated", "suspected_incomplete"]
        if result.finish_reason == "length":
            status = "truncated"
        elif not terminal or terminal[-1] not in ".!?…":
            status = "suspected_incomplete"
        else:
            status = "complete"
        return PromptResult(
            status=status,
            generation=result,
            prompt_version=PROMPT_VERSION,
            elapsed_seconds=perf_counter() - started,
        )
