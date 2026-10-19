"""Server-owned provider/model selection; never load an implicit dotenv file."""

import re
from typing import Literal
from urllib.parse import urlsplit

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ProviderName = Literal["fake", "ollama"]
MODEL_NAME = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._/-]*:[a-zA-Z0-9][a-zA-Z0-9._-]*$")


def default_models() -> dict[ProviderName, tuple[str, ...]]:
    return {"fake": ("fake-v1",), "ollama": ("llama3.2:3b",)}


class AISettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="AI_",
        env_file=None,
        extra="forbid",
        frozen=True,
        hide_input_in_errors=True,
        populate_by_name=True,
    )
    provider: ProviderName = "fake"
    model: str | None = None
    model_registry: dict[ProviderName, tuple[str, ...]] = Field(default_factory=default_models)
    timeout_seconds: float = Field(default=60, gt=0, le=120)
    max_output_tokens: int = Field(default=512, ge=1, le=1024)
    max_response_bytes: int = Field(default=65536, ge=1024, le=262144)
    max_concurrency: int = Field(default=2, ge=1, le=4)
    ollama_base_url: str = Field(
        default="http://127.0.0.1:11434", validation_alias="OLLAMA_BASE_URL", repr=False
    )
    ollama_api_key: SecretStr | None = Field(
        default=None, validation_alias="OLLAMA_API_KEY", repr=False
    )

    @field_validator("ollama_base_url")
    @classmethod
    def loopback_endpoint(cls, value: str) -> str:
        try:
            url = urlsplit(value)
            port = url.port
            valid = (
                url.scheme in {"http", "https"}
                and url.hostname in {"127.0.0.1", "::1", "localhost"}
                and (port is None or 1 <= port <= 65535)
                and url.username is None
                and url.password is None
                and url.path in {"", "/"}
                and not url.query
                and not url.fragment
                and not any(c.isspace() for c in value)
            )
        except ValueError:
            valid = False
        if not valid:
            raise ValueError("Ollama requires a loopback origin without credentials or paths")
        return value.rstrip("/")

    @field_validator("ollama_api_key")
    @classmethod
    def safe_key(cls, value: SecretStr | None) -> SecretStr | None:
        if value is not None:
            raw = value.get_secret_value()
            if not raw or len(raw) > 4096 or any(ord(c) < 33 or ord(c) > 126 for c in raw):
                raise ValueError("Invalid provider credential")
        return value

    @model_validator(mode="after")
    def selection(self) -> "AISettings":
        for name, models in self.model_registry.items():
            if not models or len(models) > 32 or len(set(models)) != len(models):
                raise ValueError("Provider model registry must be nonempty and unique")
            for model in models:
                if name == "fake":
                    if model != "fake-v1":
                        raise ValueError("Unsupported fake model")
                elif (
                    len(model) > 128 or not MODEL_NAME.fullmatch(model) or "cloud" in model.lower()
                ):
                    raise ValueError("Require explicit local model tags; cloud models are disabled")
        selected = self.model or ("fake-v1" if self.provider == "fake" else "llama3.2:3b")
        if selected not in self.model_registry.get(self.provider, ()):
            raise ValueError("Selected model is not in the server-owned provider registry")
        object.__setattr__(self, "model", selected)
        return self
