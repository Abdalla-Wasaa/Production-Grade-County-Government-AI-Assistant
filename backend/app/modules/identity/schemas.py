"""Strict public contracts; secret input never enters response serialization."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from email_validator import EmailNotValidError, validate_email
from pydantic import BaseModel, ConfigDict, Field, SecretStr, field_validator

Role = Literal["citizen", "staff", "admin"]


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, hide_input_in_errors=True)


class Login(Contract):
    email: str = Field(min_length=3, max_length=254)
    password: SecretStr = Field(min_length=1, max_length=128, repr=False)

    @field_validator("email")
    @classmethod
    def email_format(cls, value: str) -> str:
        try:
            normalized = value.strip().lower()
            candidate = normalized[:-8] + ".test" if normalized.endswith(".invalid") else normalized
            result = validate_email(candidate, check_deliverability=False, test_environment=True)
            return normalized if normalized.endswith(".invalid") else result.normalized.lower()
        except EmailNotValidError:
            raise ValueError("Invalid email") from None

    @field_validator("password")
    @classmethod
    def password_text(cls, value: SecretStr) -> SecretStr:
        raw = value.get_secret_value()
        if "\x00" in raw or any(0xD800 <= ord(char) <= 0xDFFF for char in raw):
            raise ValueError("Invalid password text")
        return value


class Activation(Contract):
    token: SecretStr = Field(min_length=43, max_length=43, repr=False)
    password: SecretStr = Field(min_length=12, max_length=128, repr=False)
    preferred_language: Literal["en", "sw"]
    privacy_notice_version: str = Field(min_length=1, max_length=64)
    privacy_notice_acknowledged: bool = Field(strict=True)

    @field_validator("privacy_notice_acknowledged")
    @classmethod
    def acknowledged(cls, value: bool) -> bool:
        if value is not True:
            raise ValueError("Notice acknowledgement required")
        return value

    @field_validator("password")
    @classmethod
    def password_text(cls, value: SecretStr) -> SecretStr:
        raw = value.get_secret_value()
        if "\x00" in raw or any(0xD800 <= ord(char) <= 0xDFFF for char in raw):
            raise ValueError("Invalid password text")
        return value


class CurrentUser(Contract):
    id: UUID
    email: str
    role: Role
    preferred_language: Literal["en", "sw"]


class TokenResponse(Contract):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: Literal[900] = 900
    user: CurrentUser


class CSRFResponse(Contract):
    csrf_token: str


class SessionItem(Contract):
    id: UUID
    created_at: datetime
    expires_at: datetime
    last_used_at: datetime
    is_current: bool


class SessionList(Contract):
    items: list[SessionItem]
    next_cursor: str | None = None
