"""Identity persistence; schema is created only by explicit Alembic revisions."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("role IN ('citizen','staff','admin')", name="ck_user_role"),
        CheckConstraint("status IN ('active','disabled')", name="ck_user_status"),
        CheckConstraint("preferred_language IN ('en','sw')", name="ck_user_language"),
        CheckConstraint("token_version >= 0", name="ck_user_version"),
        CheckConstraint("email_normalized = lower(btrim(email_normalized))", name="ck_user_email"),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    email_normalized: Mapped[str] = mapped_column(String(254), unique=True)
    password_hash: Mapped[str] = mapped_column(Text)
    role: Mapped[str] = mapped_column(String(16))
    status: Mapped[str] = mapped_column(String(16), default="active")
    preferred_language: Mapped[str] = mapped_column(String(2))
    token_version: Mapped[int] = mapped_column(default=0)
    privacy_notice_version: Mapped[str] = mapped_column(String(64))
    privacy_notice_acknowledged_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class Invitation(Base):
    __tablename__ = "invitations"
    __table_args__ = (
        CheckConstraint("purpose IN ('activation','password_reset')", name="ck_invitation_purpose"),
        CheckConstraint("role IN ('citizen','staff','admin')", name="ck_invitation_role"),
        CheckConstraint("preferred_language IN ('en','sw')", name="ck_invitation_language"),
        CheckConstraint("expires_at > created_at", name="ck_invitation_expiry"),
        CheckConstraint(
            "(purpose='activation' AND target_user_id IS NULL) OR "
            "(purpose='password_reset' AND target_user_id IS NOT NULL)",
            name="ck_invitation_target",
        ),
        Index(
            "uq_invitation_outstanding",
            "email_normalized",
            "purpose",
            unique=True,
            postgresql_where=text("consumed_at IS NULL AND revoked_at IS NULL"),
        ),
        Index("ix_invitation_expiry", "expires_at"),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    email_normalized: Mapped[str] = mapped_column(String(254))
    purpose: Mapped[str] = mapped_column(String(16))
    target_user_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    role: Mapped[str] = mapped_column(String(16))
    preferred_language: Mapped[str] = mapped_column(String(2))
    privacy_notice_version: Mapped[str] = mapped_column(String(64))
    token_digest: Mapped[str] = mapped_column(String(64), unique=True)
    issuer: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    accepted_user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )


class AuthSession(Base):
    __tablename__ = "auth_sessions"
    __table_args__ = (
        CheckConstraint("expires_at = created_at + interval '7 days'", name="ck_session_lifetime"),
        Index("ix_session_owner", "user_id", "created_at", "id"),
        Index("ix_session_expiry", "expires_at"),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    last_used_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    reason: Mapped[str | None] = mapped_column(String(32))


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    __table_args__ = (
        UniqueConstraint("session_id", "id", name="uq_refresh_family_id"),
        ForeignKeyConstraint(
            ["session_id", "replaced_by_id"],
            ["refresh_tokens.session_id", "refresh_tokens.id"],
            name="fk_refresh_successor",
            deferrable=True,
            initially="DEFERRED",
        ),
        UniqueConstraint("replaced_by_id", name="uq_refresh_successor"),
        CheckConstraint("expires_at > created_at", name="ck_refresh_expiry"),
        CheckConstraint(
            "replaced_by_id IS NULL OR consumed_at IS NOT NULL", name="ck_refresh_consumed"
        ),
        Index(
            "uq_refresh_live",
            "session_id",
            unique=True,
            postgresql_where=text("consumed_at IS NULL"),
        ),
        Index("ix_refresh_expiry", "expires_at"),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    session_id: Mapped[UUID] = mapped_column(ForeignKey("auth_sessions.id", ondelete="CASCADE"))
    token_digest: Mapped[str] = mapped_column(String(64), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    replaced_by_id: Mapped[UUID | None]


class AuthAudit(Base):
    __tablename__ = "auth_audit_events"
    __table_args__ = (
        Index("ix_audit_time", "occurred_at"),
        Index("ix_audit_subject", "subject", "occurred_at"),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    actor: Mapped[str | None] = mapped_column(String(64))
    subject: Mapped[str | None] = mapped_column(String(64))
    action: Mapped[str] = mapped_column(String(32))
    outcome: Mapped[str] = mapped_column(String(16))
    request_id: Mapped[UUID]


class AuthRateLimit(Base):
    __tablename__ = "auth_rate_limits"
    __table_args__ = (
        CheckConstraint("count >= 0", name="ck_rate_count"),
        Index("ix_rate_expiry", "expires_at"),
    )
    dimension: Mapped[str] = mapped_column(String(32), primary_key=True)
    identifier: Mapped[str] = mapped_column(String(64), primary_key=True)
    window: Mapped[int] = mapped_column(primary_key=True)
    count: Mapped[int]
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
