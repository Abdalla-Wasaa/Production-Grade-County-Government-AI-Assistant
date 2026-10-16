"""Explicit local-only settings; never discover or load coursework .env files."""

from typing import Literal
from urllib.parse import urlsplit

from pydantic import ValidationError, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict, SettingsError


class ConfigurationError(RuntimeError):
    """Application configuration could not be loaded safely."""


class Settings(BaseSettings):
    """Runtime configuration is validated at factory invocation, not import time."""

    model_config = SettingsConfigDict(
        env_prefix="COUNTY_",
        env_file=None,
        extra="forbid",
        frozen=True,
        hide_input_in_errors=True,
    )

    environment: Literal["development", "test"]
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    cors_origins: tuple[str, ...] = ()

    @field_validator("cors_origins")
    @classmethod
    def validate_origins(cls, origins: tuple[str, ...]) -> tuple[str, ...]:
        for origin in origins:
            parsed = urlsplit(origin)
            # Accessing port also rejects malformed/out-of-range port numbers.
            _ = parsed.port
            if (
                parsed.scheme not in {"http", "https"}
                or parsed.hostname not in {"localhost", "127.0.0.1", "::1"}
                or parsed.username is not None
                or parsed.password is not None
                or parsed.path
                or parsed.query
                or parsed.fragment
                or "*" in origin
                or any(character.isspace() for character in origin)
            ):
                raise ValueError("CORS requires explicit loopback origins without paths")
        if len(set(origins)) != len(origins):
            raise ValueError("CORS origins must be unique")
        return origins


def load_settings() -> Settings:
    """Do not expose Pydantic input values or JSON parsing errors at startup."""
    try:
        return Settings()
    except (ValidationError, SettingsError):
        raise ConfigurationError(
            "Invalid configuration; review COUNTY_ environment variables."
        ) from None
