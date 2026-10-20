"""Server-owned provider/model allowlists; no implicit dotenv or arbitrary endpoints."""

import re
from typing import Literal
from urllib.parse import urlsplit

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_MODEL = re.compile(
    r"^[A-Za-z0-9][A-Za-z0-9._-]*(/[A-Za-z0-9][A-Za-z0-9._-]*)*:[A-Za-z0-9][A-Za-z0-9._-]*$"
)


class AISettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="AI_",
        env_file=None,
        extra="forbid",
        frozen=True,
        hide_input_in_errors=True,
        populate_by_name=True,
    )
    provider: Literal["fake", "ollama"] = "fake"
    model: str = Field(default="fake-v1", min_length=1, max_length=128)
    allowed_models: tuple[str, ...] = ("llama3.2:3b",)
    timeout_seconds: float = Field(default=5, gt=0, le=120)
    max_output_tokens: int = Field(default=512, ge=1, le=1024)
    max_concurrency: int = Field(default=2, ge=1, le=4)
    max_response_bytes: int = Field(default=65536, ge=1024, le=262144)
    ollama_base_url: str = Field(
        default="http://127.0.0.1:11434", validation_alias="OLLAMA_BASE_URL", repr=False
    )
    ollama_api_key: SecretStr | None = Field(
        default=None, validation_alias="OLLAMA_API_KEY", repr=False
    )
    ollama_context_tokens: int = Field(
        default=8192, ge=2048, le=32768, validation_alias="OLLAMA_CONTEXT_TOKENS"
    )

    # Server-owned sampling is explicit so model-file defaults cannot bias comparisons.
    temperature: float = Field(default=0.7, ge=0, le=2, allow_inf_nan=False)
    top_p: float = Field(default=0.8, gt=0, le=1, allow_inf_nan=False)
    top_k: int = Field(default=20, ge=1, le=100, strict=True)
    min_p: float = Field(default=0, ge=0, le=1, allow_inf_nan=False)
    repeat_penalty: float = Field(default=1, ge=0.5, le=2, allow_inf_nan=False)
    seed: int = Field(default=42, ge=0, le=2147483647, strict=True)

    @field_validator(
        "temperature", "top_p", "top_k", "min_p", "repeat_penalty", "seed", mode="before"
    )
    @classmethod
    def numeric_sampling(cls, value: object) -> object:
        if isinstance(value, bool):
            raise ValueError("Sampling parameters must be numeric, not boolean")
        # Environment values are strings; strict integer fields still reject fractions.
        if isinstance(value, str) and re.fullmatch(r"[0-9]+", value):
            return int(value)
        return value

    @field_validator("ollama_base_url")
    @classmethod
    def loopback_only(cls, value: str) -> str:
        try:
            url = urlsplit(value)
            port = url.port
            valid = (
                url.scheme in {"http", "https"}
                and url.hostname in {"127.0.0.1", "::1"}
                and url.username is None
                and url.password is None
                and url.path in {"", "/"}
                and not url.query
                and not url.fragment
                and (port is None or 1 <= port <= 65535)
                and not url.netloc.endswith(":")
                and not any(c.isspace() or c in "\\%?#" for c in value)
            )
        except ValueError:
            valid = False
        if not valid:
            raise ValueError(
                "Ollama requires a numeric loopback origin without credentials or paths"
            )
        return value.rstrip("/")

    @field_validator("allowed_models")
    @classmethod
    def local_tag_allowlist(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        if not 1 <= len(values) <= 32 or len(set(values)) != len(values):
            raise ValueError("Require 1–32 unique allowed model tags")
        for value in values:
            if len(value) > 128 or not _MODEL.fullmatch(value) or "cloud" in value.lower():
                raise ValueError("Require explicit local model tags; cloud models are disabled")
        return values

    @field_validator("ollama_api_key")
    @classmethod
    def private_header(cls, value: SecretStr | None) -> SecretStr | None:
        if value is not None:
            raw = value.get_secret_value()
            if not raw or len(raw) > 4096 or any(ord(c) < 33 or ord(c) > 126 for c in raw):
                raise ValueError("Invalid Ollama gateway credential")
        return value

    @model_validator(mode="after")
    def selection(self) -> "AISettings":
        if (self.provider == "fake" and self.model != "fake-v1") or (
            self.provider == "ollama" and self.model not in self.allowed_models
        ):
            raise ValueError("Selected model is not supported by the configured provider")
        return self
