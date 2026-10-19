"""Minimal control metadata; domain content remains in its original tables."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class PrivacyOperator(Base):
    __tablename__ = "privacy_operators"
    role_name: Mapped[str] = mapped_column(String(63), primary_key=True)
    enabled: Mapped[bool] = mapped_column(default=True)
    can_hold: Mapped[bool] = mapped_column(default=False)
    can_request: Mapped[bool] = mapped_column(default=False)
    can_maintain: Mapped[bool] = mapped_column(default=False)


class PrivacyHold(Base):
    __tablename__ = "privacy_holds"
    __table_args__ = (
        CheckConstraint("scope IN ('account','conversation')", name="ck_privacy_hold_scope"),
        CheckConstraint("reason IN ('incident','records','review')", name="ck_privacy_hold_reason"),
        CheckConstraint("(scope='account') = (conversation_id IS NULL)", name="ck_hold_target"),
        CheckConstraint("review_due_at = reviewed_at + interval '30 days'", name="ck_hold_review"),
        CheckConstraint("created_at <= reviewed_at", name="ck_hold_clock"),
        CheckConstraint(
            "released_at IS NULL OR released_at >= reviewed_at", name="ck_hold_release"
        ),
        CheckConstraint("audit_subject ~ '^[a-f0-9]{64}$'", name="ck_hold_digest"),
        CheckConstraint(
            "(released_at IS NULL AND released_by IS NULL AND release_ref IS NULL) "
            "OR (released_at IS NOT NULL AND released_by IS NOT NULL AND release_ref IS NOT NULL)",
            name="ck_hold_release_fields",
        ),
        Index("ix_hold_account_active", "user_id", postgresql_where=text("released_at IS NULL")),
        Index(
            "ix_hold_review_active", "review_due_at", postgresql_where=text("released_at IS NULL")
        ),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    # Intentionally durable UUID references, not FKs that erase hold evidence on purge.
    # Creation checks the locked resource; released metadata expires after 90 days.
    user_id: Mapped[UUID]
    conversation_id: Mapped[UUID | None]
    scope: Mapped[str] = mapped_column(String(16))
    reason: Mapped[str] = mapped_column(String(16))
    case_ref: Mapped[UUID]
    audit_subject: Mapped[str] = mapped_column(String(64))
    issuer: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    reviewed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    review_due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    reviewed_by: Mapped[str] = mapped_column(String(64))
    review_ref: Mapped[UUID]
    released_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    released_by: Mapped[str | None] = mapped_column(String(64))
    release_ref: Mapped[UUID | None]


class DeletionRequest(Base):
    __tablename__ = "privacy_deletion_requests"
    __table_args__ = (
        CheckConstraint("status IN ('accepted','held','completed')", name="ck_deletion_status"),
        CheckConstraint(
            "(status='completed') = (completed_at IS NOT NULL)", name="ck_deletion_completion"
        ),
        CheckConstraint("status <> 'completed' OR user_id IS NULL", name="ck_deletion_live_user"),
        CheckConstraint("received_at <= accepted_at", name="ck_deletion_receipt"),
        CheckConstraint("target_digest ~ '^[a-f0-9]{64}$'", name="ck_deletion_digest"),
        Index("uq_deletion_user", "user_id", unique=True),
        Index("ix_deletion_due", "completion_due_at"),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True)
    user_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    target_digest: Mapped[str] = mapped_column(String(64))
    verification_ref: Mapped[UUID]
    accepted_by: Mapped[str] = mapped_column(String(64))
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    accepted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    acknowledgement_due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    completion_due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(16))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class DeletionLedger(Base):
    __tablename__ = "privacy_deletion_ledger"
    __table_args__ = (
        CheckConstraint("kind IN ('account','conversation')", name="ck_ledger_kind"),
        Index("ix_privacy_ledger_expiry", "expires_at"),
    )
    kind: Mapped[str] = mapped_column(String(16), primary_key=True)
    target_id: Mapped[UUID] = mapped_column(primary_key=True)
    deleted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class MaintenanceState(Base):
    __tablename__ = "privacy_maintenance_state"
    __table_args__ = (CheckConstraint("id=1", name="ck_privacy_state_singleton"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    audit_key_sha256: Mapped[str | None] = mapped_column(String(64))
    last_daily_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_success_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_hold_alert_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
