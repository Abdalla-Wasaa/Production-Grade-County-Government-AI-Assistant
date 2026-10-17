"""Identity transactions: user then family then token locks; no external services."""

from datetime import timedelta
from typing import Literal, cast
from uuid import UUID, uuid4

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.identity.models import AuthSession, Invitation, RefreshToken, User
from app.modules.identity.repository import audit, counter, lock_user, revoke_all
from app.modules.identity.schemas import (
    Activation,
    CurrentUser,
    Login,
    Role,
    SessionItem,
    SessionList,
    TokenResponse,
)
from app.modules.identity.security import AuthFailure, Passwords, Tokens, digest, random_token


class Identity:
    def __init__(self, db: AsyncSession, tokens: Tokens, passwords: Passwords, request_id: UUID):
        self.db, self.tokens, self.passwords, self.request_id = db, tokens, passwords, request_id

    async def event(self, action: str, outcome: str, subject: str | None = None) -> None:
        await audit(self.db, self.tokens, action, outcome, self.request_id, subject, actor=subject)

    def public_user(self, user: User) -> CurrentUser:
        return CurrentUser(
            id=user.id,
            email=user.email_normalized,
            role=cast(Role, user.role),
            preferred_language=cast(Literal["en", "sw"], user.preferred_language),
        )  # refined by DB CHECK

    async def refresh_record(self, raw: str | None) -> RefreshToken | None:
        if not raw:
            return None
        try:
            value = digest(raw)
        except AuthFailure:
            return None
        return (
            await self.db.execute(select(RefreshToken).where(RefreshToken.token_digest == value))
        ).scalar_one_or_none()

    async def cookie_family(self, raw: str | None) -> AuthSession | None:
        row = await self.refresh_record(raw)
        family = await self.db.get(AuthSession, row.session_id) if row else None
        if family is None or family.revoked_at or family.expires_at <= self.tokens.clock():
            return None
        user = await self.db.get(User, family.user_id)
        return family if user and user.status == "active" else None

    async def authenticate(self, raw: str) -> tuple[User, AuthSession]:
        claims = self.tokens.decode_access(raw)
        user = await lock_user(self.db, UUID(claims["sub"]))
        family = (
            await self.db.execute(
                select(AuthSession)
                .where(AuthSession.id == UUID(claims["sid"]))
                .with_for_update()
                .execution_options(populate_existing=True)
            )
        ).scalar_one_or_none()
        if (
            user is None
            or user.status != "active"
            or user.token_version != claims["token_version"]
            or family is None
            or family.user_id != user.id
            or family.revoked_at
            or family.expires_at <= self.tokens.clock()
        ):
            raise AuthFailure()
        family.last_used_at = self.tokens.clock()
        return user, family

    async def activate(self, body: Activation) -> None:
        if body.privacy_notice_version != self.tokens.config.privacy_notice_version:
            raise AuthFailure(422, "validation_error")
        value = digest(body.token.get_secret_value())
        # Expensive work has no row lock; state is rechecked afterward.
        encoded = await self.passwords.hash(body.password.get_secret_value())
        invitation = (
            await self.db.execute(select(Invitation).where(Invitation.token_digest == value))
        ).scalar_one_or_none()
        if invitation is None:
            raise AuthFailure(400, "invitation_invalid")
        user = (
            await lock_user(self.db, invitation.target_user_id)
            if invitation.target_user_id
            else None
        )
        invitation = (
            await self.db.execute(
                select(Invitation)
                .where(Invitation.id == invitation.id)
                .with_for_update()
                .execution_options(populate_existing=True)
            )
        ).scalar_one()
        now = self.tokens.clock()
        if invitation.revoked_at or invitation.consumed_at or invitation.expires_at <= now:
            raise AuthFailure(400, "invitation_invalid")
        if invitation.purpose == "activation":
            exists = (
                await self.db.execute(
                    select(User.id).where(User.email_normalized == invitation.email_normalized)
                )
            ).scalar_one_or_none()
            if exists:
                raise AuthFailure(400, "invitation_invalid")
            user = User(
                id=uuid4(),
                email_normalized=invitation.email_normalized,
                password_hash=encoded,
                role=invitation.role,
                status="active",
                preferred_language=body.preferred_language,
                token_version=0,
                privacy_notice_version=body.privacy_notice_version,
                privacy_notice_acknowledged_at=now,
                created_at=now,
                updated_at=now,
            )
            self.db.add(user)
            await self.db.flush()
        elif (
            user
            and user.status == "active"
            and user.email_normalized == invitation.email_normalized
        ):
            await revoke_all(self.db, user, self.tokens, "password_reset")
            user.password_hash = encoded
            user.preferred_language = body.preferred_language
            user.privacy_notice_version = body.privacy_notice_version
            user.privacy_notice_acknowledged_at = now
        else:
            raise AuthFailure(400, "invitation_invalid")
        invitation.consumed_at, invitation.accepted_user_id = now, user.id
        await self.event(invitation.purpose, "success", str(user.id))

    async def login(self, body: Login) -> tuple[TokenResponse, str, AuthSession]:
        user = (
            await self.db.execute(select(User).where(User.email_normalized == body.email))
        ).scalar_one_or_none()
        # End read transaction before hashing; compare identity/hash again under lock.
        snapshot = (user.id, user.password_hash) if user else None
        await self.db.rollback()
        verified = await self.passwords.verify(
            body.password.get_secret_value(), snapshot[1] if snapshot else None
        )
        if snapshot:
            user = await lock_user(self.db, snapshot[0])
        if (
            not verified
            or user is None
            or user.status != "active"
            or snapshot is None
            or user.password_hash != snapshot[1]
        ):
            raise AuthFailure()
        if self.passwords.hasher.check_needs_rehash(user.password_hash):
            # Current parameters are fixed; rehash without holding locks if changed.
            await self.db.rollback()
            encoded = await self.passwords.hash(body.password.get_secret_value())
            user = await lock_user(self.db, snapshot[0])
            if user is None or user.status != "active" or user.password_hash != snapshot[1]:
                raise AuthFailure()
            user.password_hash = encoded
            user.updated_at = self.tokens.clock()
        now = self.tokens.clock()
        family = AuthSession(
            id=uuid4(),
            user_id=user.id,
            created_at=now,
            expires_at=now + timedelta(days=7),
            last_used_at=now,
        )
        self.db.add(family)
        await self.db.flush()
        raw = random_token()
        self.db.add(
            RefreshToken(
                id=uuid4(),
                session_id=family.id,
                token_digest=digest(raw),
                created_at=now,
                expires_at=family.expires_at,
            )
        )
        await self.event("login", "success", str(user.id))
        response = TokenResponse(
            access_token=self.tokens.access(user.id, family.id, user.token_version),
            user=self.public_user(user),
        )
        return response, raw, family

    async def rotate(self, raw: str | None) -> tuple[TokenResponse, str, AuthSession]:
        record = await self.refresh_record(raw)
        if record is None:
            raise AuthFailure()
        family_snapshot = await self.db.get(AuthSession, record.session_id)
        if family_snapshot is None:
            raise AuthFailure()
        user = await lock_user(self.db, family_snapshot.user_id)
        family = (
            await self.db.execute(
                select(AuthSession)
                .where(AuthSession.id == record.session_id)
                .with_for_update()
                .execution_options(populate_existing=True)
            )
        ).scalar_one_or_none()
        record = (
            await self.db.execute(
                select(RefreshToken)
                .where(RefreshToken.id == record.id)
                .with_for_update()
                .execution_options(populate_existing=True)
            )
        ).scalar_one_or_none()
        now = self.tokens.clock()
        if (
            user is None
            or user.status != "active"
            or family is None
            or family.revoked_at
            or family.expires_at <= now
            or record is None
            or record.expires_at <= now
        ):
            raise AuthFailure()
        if record.consumed_at:
            family.revoked_at, family.reason = now, "refresh_reuse"
            await self.event("refresh_reuse", "revoked", str(user.id))
            # The HTTP boundary commits AuthFailure, preserving this revocation.
            raise AuthFailure()
        record.consumed_at = now
        await self.db.flush()  # release the partial unique live-token slot first
        next_id, next_raw = uuid4(), random_token()
        self.db.add(
            RefreshToken(
                id=next_id,
                session_id=family.id,
                token_digest=digest(next_raw),
                created_at=now,
                expires_at=family.expires_at,
            )
        )
        record.replaced_by_id = next_id
        family.last_used_at = now
        await self.event("refresh", "success", str(user.id))
        return (
            TokenResponse(
                access_token=self.tokens.access(user.id, family.id, user.token_version),
                user=self.public_user(user),
            ),
            next_raw,
            family,
        )

    async def logout(self, raw: str | None) -> None:
        row = await self.refresh_record(raw)
        snapshot = await self.db.get(AuthSession, row.session_id) if row else None
        if snapshot:
            await lock_user(self.db, snapshot.user_id)
            family = (
                await self.db.execute(
                    select(AuthSession)
                    .where(AuthSession.id == snapshot.id)
                    .with_for_update()
                    .execution_options(populate_existing=True)
                )
            ).scalar_one()
            if family.revoked_at is None:
                family.revoked_at, family.reason = self.tokens.clock(), "logout"
        await self.event("logout", "success", str(snapshot.user_id) if snapshot else None)

    async def sessions(
        self, user: User, current: AuthSession, limit: int, cursor: str | None
    ) -> SessionList:
        query = select(AuthSession).where(
            AuthSession.user_id == user.id,
            AuthSession.revoked_at.is_(None),
            AuthSession.expires_at > self.tokens.clock(),
        )
        if cursor:
            try:
                data = self.tokens.context(cursor, "sessions_cursor", str(user.id))
                from datetime import datetime

                created = datetime.fromisoformat(data["created_at"])
                key = UUID(data["id"])
                if created.tzinfo is None:
                    raise ValueError
            except (AuthFailure, ValueError, KeyError, TypeError):
                raise AuthFailure(422, "validation_error") from None
            query = query.where(
                or_(
                    AuthSession.created_at < created,
                    and_(AuthSession.created_at == created, AuthSession.id < key),
                )
            )
        rows = list(
            (
                await self.db.scalars(
                    query.order_by(AuthSession.created_at.desc(), AuthSession.id.desc()).limit(
                        limit + 1
                    )
                )
            ).all()
        )
        next_cursor = None
        if len(rows) > limit:
            rows = rows[:limit]
            last = rows[-1]
            next_cursor = self.tokens.sign_context(
                "sessions_cursor",
                str(user.id),
                300,
                created_at=last.created_at.isoformat(),
                id=str(last.id),
            )
        return SessionList(
            items=[
                SessionItem(
                    id=row.id,
                    created_at=row.created_at,
                    expires_at=row.expires_at,
                    last_used_at=row.last_used_at,
                    is_current=row.id == current.id,
                )
                for row in rows
            ],
            next_cursor=next_cursor,
        )

    async def revoke_session(self, user: User, session_id: UUID) -> None:
        row = (
            await self.db.execute(
                select(AuthSession)
                .where(
                    AuthSession.id == session_id,
                    AuthSession.user_id == user.id,
                    AuthSession.revoked_at.is_(None),
                    AuthSession.expires_at > self.tokens.clock(),
                )
                .with_for_update()
            )
        ).scalar_one_or_none()
        if row is None:
            raise AuthFailure(404, "not_found")
        row.revoked_at, row.reason = self.tokens.clock(), "user_revoked"
        await self.event("session_revoke", "success", str(user.id))

    async def logout_all(self, user: User) -> None:
        await revoke_all(self.db, user, self.tokens, "logout_all")
        await self.event("logout_all", "success", str(user.id))

    async def admission(self, ip: str, kind: str) -> None:
        # Bound attacker-created account dimensions before password work.
        specs = {
            "csrf": (60, 60),
            "activation": (900, 5),
            "refresh": (60, 60),
            "login": (60, 60),
            "mutation": (60, 60),
        }
        seconds, limit = specs[kind]
        await counter(self.db, self.tokens, kind + "_admission", ip, seconds, limit)
        await self.db.commit()
