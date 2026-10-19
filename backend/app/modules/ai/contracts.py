"""Provider-neutral, bounded text contracts. All content is untrusted and private."""

from enum import StrEnum
from typing import Literal, Protocol

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True, strict=True)


class Message(Contract):
    role: Literal["system", "user", "assistant"]
    content: str = Field(min_length=1, max_length=8000, repr=False)

    @model_validator(mode="after")
    def nonblank(self) -> "Message":
        if not self.content.strip():
            raise ValueError("Message must contain text")
        return self


class GenerationRequest(Contract):
    messages: tuple[Message, ...] = Field(min_length=1, max_length=32, repr=False)
    language: Literal["en", "sw"] = "en"
    max_output_tokens: int = Field(default=256, ge=1, le=1024)

    @model_validator(mode="after")
    def bounded_context(self) -> "GenerationRequest":
        if sum(len(message.content) for message in self.messages) > 24000:
            raise ValueError("Message context exceeds the character budget")
        if self.messages[-1].role != "user":
            raise ValueError("The final message must be from the user")
        return self


class Usage(Contract):
    # Unknown is explicit. Fake responses never fabricate measured token usage.
    input_tokens: int | None = Field(default=None, ge=0)
    output_tokens: int | None = Field(default=None, ge=0)


class ModelIdentity(Contract):
    provider: str = Field(pattern=r"^[a-z][a-z0-9_-]{0,31}$")
    model: str = Field(min_length=1, max_length=128)


class GenerationResult(Contract):
    content: str = Field(min_length=1, max_length=16000, repr=False)
    identity: ModelIdentity
    usage: Usage
    finish_reason: Literal["stop", "length"]
    synthetic: bool


class ErrorCode(StrEnum):
    UNAVAILABLE = "provider_unavailable"
    TIMEOUT = "provider_timeout"
    MODEL_NOT_FOUND = "model_not_found"
    RATE_LIMITED = "provider_rate_limited"
    REJECTED = "provider_request_rejected"
    INVALID_RESPONSE = "invalid_provider_response"
    INVALID_REQUEST = "invalid_provider_request"


class ProviderError(RuntimeError):
    """Only a fixed code is exposed; never retain upstream bodies, URLs or secrets."""

    def __init__(self, code: ErrorCode) -> None:
        self.code = code
        self.retryable = code in {ErrorCode.UNAVAILABLE, ErrorCode.TIMEOUT, ErrorCode.RATE_LIMITED}
        super().__init__(code.value)


class AIProvider(Protocol):
    async def generate(self, request: GenerationRequest) -> GenerationResult: ...

    async def aclose(self) -> None: ...
