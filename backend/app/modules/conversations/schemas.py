"""Strict public DTOs: ownership/roles/counters can never be mass assigned."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

Language = Literal["en", "sw"]


def clean_text(value: str, maximum: int) -> str:
    value = value.strip()
    if not value or len(value) > maximum or "\x00" in value:
        raise ValueError("Invalid text")
    try:
        value.encode("utf-8", errors="strict")
    except UnicodeError:
        raise ValueError("Invalid text") from None
    return value


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, from_attributes=True)


class CreateConversation(Contract):
    title: str | None = Field(default=None, strict=True, max_length=120)
    language: Language | None = None

    @field_validator("title")
    @classmethod
    def title_text(cls, value: str | None) -> str | None:
        return clean_text(value, 120) if value is not None else None

    @model_validator(mode="after")
    def no_explicit_null(self) -> "CreateConversation":
        if any(getattr(self, key) is None for key in self.model_fields_set):
            raise ValueError("Null fields are not supported")
        return self


class UpdateConversation(CreateConversation):
    @model_validator(mode="after")
    def nonempty(self) -> "UpdateConversation":
        if not self.model_fields_set:
            raise ValueError("At least one field required")
        return self


class AddMessage(Contract):
    content: str = Field(strict=True, min_length=1, max_length=4000)

    @field_validator("content")
    @classmethod
    def message_text(cls, value: str) -> str:
        return clean_text(value, 4000)


class ConversationItem(Contract):
    id: UUID
    title: str
    language: Language
    version: int
    created_at: datetime
    updated_at: datetime
    expires_at: datetime


class MessageItem(Contract):
    id: UUID
    conversation_id: UUID
    sequence: int
    role: Literal["user"]
    content: str
    language: Language
    created_at: datetime


class ConversationList(Contract):
    items: list[ConversationItem]
    next_cursor: str | None


class MessageList(Contract):
    items: list[MessageItem]
    next_cursor: str | None
