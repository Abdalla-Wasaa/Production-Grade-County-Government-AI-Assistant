"""Phase 2 persistence constraints; explicit migrations own schema creation."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Conversation(Base):
    __tablename__ = "conversations"
    __table_args__ = (
        CheckConstraint(
            "char_length(btrim(title)) BETWEEN 1 AND 120", name="ck_conversation_title"
        ),
        CheckConstraint("language IN ('en','sw')", name="ck_conversation_language"),
        CheckConstraint("next_sequence >= 1 AND version >= 1", name="ck_conversation_counters"),
        CheckConstraint(
            "created_at <= last_activity_at AND last_activity_at <= updated_at "
            "AND expires_at > last_activity_at "
            "AND expires_at <= created_at + interval '90 days'",
            name="ck_conversation_times",
        ),
        Index("ix_conversation_owner", "user_id", "updated_at", "id"),
        Index("ix_conversation_expiry", "expires_at"),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(120))
    language: Mapped[str] = mapped_column(String(2))
    next_sequence: Mapped[int] = mapped_column(BigInteger, default=1)
    version: Mapped[int] = mapped_column(BigInteger, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    last_activity_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class Message(Base):
    __tablename__ = "messages"
    __table_args__ = (
        UniqueConstraint("conversation_id", "sequence", name="uq_message_sequence"),
        UniqueConstraint("conversation_id", "client_request_id", name="uq_message_request"),
        CheckConstraint("sequence >= 1", name="ck_message_sequence"),
        CheckConstraint("role = 'user'", name="ck_message_role"),
        CheckConstraint("language IN ('en','sw')", name="ck_message_language"),
        CheckConstraint(
            "char_length(btrim(content)) BETWEEN 1 AND 4000", name="ck_message_content"
        ),
        CheckConstraint("request_hash ~ '^[0-9a-f]{64}$'", name="ck_message_hash"),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    conversation_id: Mapped[UUID] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE")
    )
    sequence: Mapped[int] = mapped_column(BigInteger)
    role: Mapped[str] = mapped_column(String(16))
    content: Mapped[str] = mapped_column(Text)
    language: Mapped[str] = mapped_column(String(2))
    client_request_id: Mapped[UUID]
    request_hash: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
