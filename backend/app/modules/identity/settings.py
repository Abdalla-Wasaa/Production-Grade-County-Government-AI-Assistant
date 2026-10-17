"""Validated, explicitly enabled authentication configuration; no env-file discovery."""

import base64
from pathlib import Path
from urllib.parse import urlsplit

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AuthSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="COUNTY_AUTH_",
        env_file=None,
        extra="forbid",
        hide_input_in_errors=True,
        frozen=True,
    )
    signing_secret: SecretStr = Field(repr=False)
    csrf_secret: SecretStr = Field(repr=False)
    throttle_secret: SecretStr = Field(repr=False)
    issuer: str = Field(min_length=1, max_length=128)
    audience: str = Field(min_length=1, max_length=128)
    origins: tuple[str, ...]
    cookie_secure: bool = True
    privacy_notice_version: str = Field(min_length=1, max_length=64)
    password_blocklist: Path
    password_blocklist_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    # One hash at a time per process; additional requests fail closed, not queue forever.
    hash_concurrency: int = Field(default=1, ge=1, le=2)
    trusted_proxy_addresses: tuple[str, ...] = ()

    @model_validator(mode="after")
    def secure_values(self) -> "AuthSettings":
        secrets = []
        for value in (self.signing_secret, self.csrf_secret, self.throttle_secret):
            try:
                decoded = base64.b64decode(value.get_secret_value(), validate=True)
            except ValueError:
                raise ValueError("Authentication secrets must be base64 random bytes") from None
            if len(decoded) < 32 or len(set(decoded)) < 16:
                raise ValueError("Authentication secrets require at least 32 random bytes")
            secrets.append(decoded)
        if len(set(secrets)) != 3:
            raise ValueError("Authentication secrets must be independent")
        if not self.origins:
            raise ValueError("Explicit browser origins are required")
        for origin in self.origins:
            parsed = urlsplit(origin)
            if (
                parsed.scheme not in {"http", "https"}
                or not parsed.hostname
                or parsed.username
                or parsed.password
                or parsed.path
                or parsed.query
                or parsed.fragment
                or "*" in origin
            ):
                raise ValueError("Invalid browser origin")
            if (not self.cookie_secure or parsed.scheme == "http") and parsed.hostname not in {
                "127.0.0.1",
                "localhost",
                "::1",
            }:
                raise ValueError("Insecure cookies/HTTP permitted only on loopback")
        return self
