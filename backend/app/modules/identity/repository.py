"""Parameterized identity queries; caller owns commit and lock ordering."""

from datetime import timedelta
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.identity.models import AuthAudit, AuthRateLimit, AuthSession, User
from app.modules.identity.security import AuthFailure, Tokens


async def audit(
    db: AsyncSession,
    tokens: Tokens,
    action: str,
    outcome: str,
    request_id: UUID,
    subject: str | None = None,
    actor: str | None = None,
) -> None:
    db.add(
        AuthAudit(
            occurred_at=tokens.clock(),
            actor=tokens.pseudonym(actor) if actor else None,
            subject=tokens.pseudonym(subject) if subject else None,
            action=action,
            outcome=outcome,
            request_id=request_id,
        )
    )
    await db.flush()


async def counter(
    db: AsyncSession, tokens: Tokens, dimension: str, identifier: str, seconds: int, limit: int
) -> None:
    now = tokens.clock()
    window = int(now.timestamp()) // seconds
    statement = insert(AuthRateLimit).values(
        dimension=dimension,
        identifier=tokens.pseudonym(identifier),
        window=window,
        count=1,
        expires_at=now + timedelta(seconds=seconds * 2),
    )
    returning = statement.on_conflict_do_update(
        index_elements=[AuthRateLimit.dimension, AuthRateLimit.identifier, AuthRateLimit.window],
        set_={"count": AuthRateLimit.count + 1},
    ).returning(AuthRateLimit.count)
    count = (await db.execute(returning)).scalar_one()
    if count > limit:
        failure = AuthFailure(429, "rate_limited", max(1, seconds - int(now.timestamp()) % seconds))
        # Record the first threshold crossing, not an unbounded audit row per retry.
        failure.record_audit = count == limit + 1
        raise failure


async def lock_user(db: AsyncSession, user_id: UUID) -> User | None:
    return (
        await db.execute(
            select(User)
            .where(User.id == user_id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
    ).scalar_one_or_none()


async def revoke_all(db: AsyncSession, user: User, tokens: Tokens, reason: str) -> None:
    user.token_version += 1
    user.updated_at = tokens.clock()
    await db.execute(
        update(AuthSession)
        .where(AuthSession.user_id == user.id, AuthSession.revoked_at.is_(None))
        .values(revoked_at=tokens.clock(), reason=reason)
    )
