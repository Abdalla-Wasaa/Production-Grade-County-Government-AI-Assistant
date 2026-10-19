"""Strict non-content operator contracts and deterministic scheduling policy."""

from datetime import UTC, datetime, time, timedelta
from typing import Literal
from uuid import UUID
from zoneinfo import ZoneInfo

from pydantic import BaseModel, ConfigDict, field_validator


class HoldCommand(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)
    id: UUID
    scope: Literal["account", "conversation"]
    target_id: UUID
    reason: Literal["incident", "records", "review"]
    case_ref: UUID


class DeleteAccountCommand(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)
    id: UUID
    user_id: UUID
    verification_ref: UUID
    verified: Literal[True]
    received_at: datetime | None = None

    @field_validator("received_at")
    @classmethod
    def aware_receipt(cls, value: datetime | None) -> datetime | None:
        if value is not None and value.tzinfo is None:
            raise ValueError("Timezone required")
        return value


class MaintenanceReport(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: Literal["idle", "busy", "completed", "attention"]
    conversations: int = 0
    accounts: int = 0
    overdue_holds: int = 0
    overdue_requests: int = 0
    backlog: bool = False
    deadline_breached: bool = False


def daily_target(now: datetime) -> datetime:
    if now.tzinfo is None:
        raise ValueError("Timezone required")
    local = now.astimezone(ZoneInfo("Africa/Nairobi"))
    target = datetime.combine(local.date(), time(2), local.tzinfo)
    if local < target:
        target -= timedelta(days=1)
    return target.astimezone(UTC)


def acknowledgement_target(now: datetime) -> datetime:
    # Synthetic target: working days are Monday-Friday, no unapproved holiday list.
    days = 0
    target = now.astimezone(ZoneInfo("Africa/Nairobi"))
    while days < 2:
        target += timedelta(days=1)
        if target.weekday() < 5:
            days += 1
    return target.astimezone(UTC)
