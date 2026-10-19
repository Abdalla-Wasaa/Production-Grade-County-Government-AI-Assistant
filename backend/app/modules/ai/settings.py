"""Server-owned provider selection; only implemented providers can be configured."""

from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AISettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="AI_", env_file=None, extra="forbid", frozen=True, hide_input_in_errors=True
    )
    provider: Literal["fake"] = "fake"
    model: Literal["fake-v1"] = "fake-v1"
    timeout_seconds: float = Field(default=5, gt=0, le=120)
    max_output_tokens: int = Field(default=512, ge=1, le=1024)
    max_concurrency: int = Field(default=2, ge=1, le=4)
