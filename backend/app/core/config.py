"""Explicit local-only settings; never discover or load coursework .env files."""

from typing import Literal
from urllib.parse import urlsplit

from pydantic import Field, SecretStr, ValidationError, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict, SettingsError
from sqlalchemy.engine import make_url


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
    auth_enabled: bool = False
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    cors_origins: tuple[str, ...] = ()

    database_url: SecretStr | None = Field(default=None, repr=False)
    db_connect_timeout_seconds: int = Field(default=5, ge=2, le=60)
    db_pool_timeout_seconds: float = Field(default=5, gt=0, le=60)
    db_pool_size: int = Field(default=5, ge=1, le=20)
    db_max_overflow: int = Field(default=5, ge=0, le=20)
    db_readiness_timeout_seconds: float = Field(default=10, gt=0, le=60)

    @field_validator("database_url")
    @classmethod
    def validate_url(cls, value: SecretStr | None) -> SecretStr | None:
        if value is not None:
            validate_database_url(value)
        return value

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


def validate_database_url(value: SecretStr) -> None:
    """Validate explicit PostgreSQL targets without echoing driver parse failures."""
    try:
        url = make_url(value.get_secret_value())
        if (
            url.drivername != "postgresql+psycopg"
            or not url.host
            or not url.database
            or not url.username
            or not url.password
            or (url.port is not None and not 1 <= url.port <= 65535)
            or set(url.query) - {"sslmode", "sslrootcert"}
            or (
                "sslmode" in url.query
                and url.query["sslmode"] not in {"disable", "require", "verify-ca", "verify-full"}
            )
            or any(c.isspace() or c in {",", "/"} for c in url.host)
        ):
            raise ValueError
    except Exception:
        raise ValueError("Invalid PostgreSQL configuration") from None
