"""Account-first transactions; caller commits, including audit and revocation."""

import hashlib
import hmac
from collections.abc import Callable
from datetime import datetime, timedelta
from uuid import UUID, uuid4

from sqlalchemy import delete, exists, func, or_, select, text, tuple_
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.conversations.models import Conversation
from app.modules.identity.models import AuthAudit, AuthRateLimit, AuthSession, Invitation, User
from app.modules.identity.repository import audit, lock_user, revoke_all
from app.modules.identity.security import AuthFailure, utcnow
from app.modules.privacy.models import (
    DeletionLedger,
    DeletionRequest,
    MaintenanceState,
    PrivacyHold,
    PrivacyOperator,
)
from app.modules.privacy.schemas import (
    DeleteAccountCommand,
    HoldCommand,
    MaintenanceReport,
    acknowledgement_target,
    daily_target,
)

MAINTENANCE_LOCK = 724051902


def operator_digest(role: str) -> str:
    return hashlib.sha256(role.encode()).hexdigest()


async def conversation_held(db: AsyncSession, user: UUID, item: UUID) -> bool:
    return bool(
        await db.scalar(
            text("SELECT public.privacy_is_held(:owner,:item)"), {"owner": user, "item": item}
        )
    )


class Privacy:
    def __init__(
        self,
        db: AsyncSession,
        key: bytes,
        clock: Callable[[], datetime] = utcnow,
    ):
        if len(key) < 32:
            raise ValueError("Invalid privacy audit key")
        self.db, self.key, self.clock = db, key, clock

    def pseudonym(self, value: str) -> str:
        return hmac.new(self.key, value.encode(), hashlib.sha256).hexdigest()

    async def authorize(self, capability: str) -> str:
        if capability not in {"can_hold", "can_request", "can_maintain", "read"}:
            raise AuthFailure(403, "forbidden")
        session, effective = (await self.db.execute(text("SELECT session_user,current_user"))).one()
        if not await self.db.scalar(
            text("SELECT has_table_privilege(session_user,'public.privacy_operators','SELECT')")
        ):
            raise AuthFailure(403, "forbidden")
        principal = await self.db.get(PrivacyOperator, session, populate_existing=True)
        if (
            session != effective
            or principal is None
            or not principal.enabled
            or (capability != "read" and not getattr(principal, capability))
            or (
                capability == "read"
                and not (principal.can_hold or principal.can_request or principal.can_maintain)
            )
        ):
            raise AuthFailure(403, "forbidden")
        state = await self.db.get(MaintenanceState, 1, populate_existing=True)
        if state is None or state.audit_key_sha256 != hashlib.sha256(self.key).hexdigest():
            raise AuthFailure(503, "service_unavailable")
        return str(session)

    async def active_hold(self, user_id: UUID) -> bool:
        return bool(
            await self.db.scalar(
                select(
                    exists().where(
                        PrivacyHold.user_id == user_id, PrivacyHold.released_at.is_(None)
                    )
                )
            )
        )

    async def create_hold(self, command: HoldCommand) -> PrivacyHold:
        role = await self.authorize("can_hold")
        await self.db.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": MAINTENANCE_LOCK})
        user_id = command.target_id
        if command.scope == "conversation":
            owner = await self.db.scalar(
                select(Conversation.user_id).where(Conversation.id == command.target_id)
            )
            if owner is None:
                raise AuthFailure(404, "not_found")
            user_id = owner
        if (
            await self.db.scalar(select(User.id).where(User.id == user_id).with_for_update())
            is None
        ):
            raise AuthFailure(404, "not_found")
        existing = await self.db.get(PrivacyHold, command.id)
        conversation_id = command.target_id if command.scope == "conversation" else None
        if existing:
            if (existing.user_id, existing.conversation_id, existing.reason, existing.case_ref) != (
                user_id,
                conversation_id,
                command.reason,
                command.case_ref,
            ):
                raise AuthFailure(409, "idempotency_conflict")
            return existing
        if (
            conversation_id
            and await self.db.scalar(
                # The account lock above and the database hold/delete guards
                # serialize this target; no extra conversation UPDATE grant needed.
                select(Conversation.id).where(
                    Conversation.id == conversation_id, Conversation.user_id == user_id
                )
            )
            is None
        ):
            raise AuthFailure(404, "not_found")
        now = self.clock()
        row = PrivacyHold(
            id=command.id,
            user_id=user_id,
            conversation_id=conversation_id,
            scope=command.scope,
            reason=command.reason,
            case_ref=command.case_ref,
            audit_subject=self.pseudonym(str(user_id)),
            issuer=operator_digest(role),
            created_at=now,
            reviewed_at=now,
            review_due_at=now + timedelta(days=30),
            reviewed_by=operator_digest(role),
            review_ref=command.case_ref,
        )
        self.db.add(row)
        await self.db.flush()  # The database trigger writes the mandatory hold audit.
        return row

    async def change_hold(self, key: UUID, case_ref: UUID, *, release: bool) -> PrivacyHold:
        role = await self.authorize("can_hold")
        await self.db.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": MAINTENANCE_LOCK})
        owner = await self.db.scalar(select(PrivacyHold.user_id).where(PrivacyHold.id == key))
        if owner is None:
            raise AuthFailure(404, "not_found")
        await self.db.execute(select(User.id).where(User.id == owner).with_for_update())
        row = await self.db.scalar(
            select(PrivacyHold)
            .where(PrivacyHold.id == key)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
        if row is None:
            raise AuthFailure(404, "not_found")
        if row.released_at is not None:
            if release:
                return row
            raise AuthFailure(409, "deletion_restricted")
        now = max(self.clock(), row.reviewed_at)
        if release:
            row.released_at, row.released_by, row.release_ref = now, operator_digest(role), case_ref
        else:
            row.reviewed_at, row.review_due_at = now, now + timedelta(days=30)
            row.reviewed_by, row.review_ref = operator_digest(role), case_ref
        await self.db.flush()
        return row

    async def request_deletion(self, command: DeleteAccountCommand) -> DeletionRequest:
        role = await self.authorize("can_request")
        if command.received_at is not None and command.received_at > self.clock():
            raise AuthFailure(422, "validation_error")
        # Serialize even two request keys for one user. An idempotent replay after
        # physical deletion remains available by digest without reviving an account.
        await self.db.execute(
            text("SELECT pg_advisory_xact_lock(:key)"),
            {"key": int(self.pseudonym(str(command.user_id))[:15], 16)},
        )
        existing = await self.db.get(DeletionRequest, command.id)
        target = self.pseudonym(str(command.user_id))
        if existing:
            if (existing.target_digest, existing.verification_ref) != (
                target,
                command.verification_ref,
            ) or (command.received_at is not None and command.received_at != existing.received_at):
                raise AuthFailure(409, "idempotency_conflict")
            return existing
        user = await lock_user(self.db, command.user_id)
        if user is None:
            raise AuthFailure(404, "not_found")
        canonical = await self.db.scalar(
            select(DeletionRequest).where(DeletionRequest.user_id == user.id)
        )
        if canonical:
            return canonical
        await revoke_all(self.db, user, self, "privacy_deletion")
        user.status = "disabled"
        now = self.clock()
        row = DeletionRequest(
            id=command.id,
            user_id=user.id,
            target_digest=target,
            verification_ref=command.verification_ref,
            accepted_by=operator_digest(role),
            received_at=command.received_at or now,
            accepted_at=now,
            acknowledgement_due_at=acknowledgement_target(command.received_at or now),
            completion_due_at=now + timedelta(days=7),
            status="held" if await self.active_hold(user.id) else "accepted",
        )
        self.db.add(row)
        await self.db.flush()  # Database insert trigger audits the accepted request atomically.
        return row

    async def request_status(self, key: UUID) -> DeletionRequest:
        await self.authorize("read")
        row = await self.db.get(DeletionRequest, key)
        if row is None:
            raise AuthFailure(404, "not_found")
        return row

    async def holds_due(self) -> list[tuple[UUID, datetime]]:
        await self.authorize("can_hold")
        rows = (
            await self.db.execute(
                select(PrivacyHold.id, PrivacyHold.review_due_at)
                .where(PrivacyHold.released_at.is_(None), PrivacyHold.review_due_at <= self.clock())
                .order_by(PrivacyHold.review_due_at, PrivacyHold.id)
                .limit(100)
            )
        ).all()
        return [(row.id, row.review_due_at) for row in rows]

    async def _remove_conversations(self, user_id: UUID, limit: int, *, expired: bool) -> int:
        query = select(Conversation.id).where(
            Conversation.user_id == user_id,
            ~func.public.privacy_is_held(Conversation.user_id, Conversation.id),
        )
        if expired:
            query = query.where(Conversation.expires_at <= self.clock())
        rows = (
            await self.db.scalars(
                query.order_by(Conversation.id).limit(limit).with_for_update(skip_locked=True)
            )
        ).all()
        count = 0
        for key in rows:
            if not await conversation_held(self.db, user_id, key):
                await self.db.execute(delete(Conversation).where(Conversation.id == key))
                count += 1
        return count

    async def _complete_requests(self, limit: int, role: str) -> tuple[int, int]:
        rows = (
            await self.db.execute(
                select(DeletionRequest.id, DeletionRequest.user_id)
                .where(
                    DeletionRequest.status != "completed",
                    # Fully held requests must not monopolize a bounded batch.
                    # Reconsider them when a hold is released or unheld data exists.
                    text("""(privacy_deletion_requests.user_id IS NULL
                      OR NOT EXISTS(SELECT FROM privacy_holds h
                        WHERE h.user_id=privacy_deletion_requests.user_id
                          AND h.released_at IS NULL)
                      OR EXISTS(SELECT FROM conversations c
                        WHERE c.user_id=privacy_deletion_requests.user_id
                          AND NOT public.privacy_is_held(c.user_id,c.id)))"""),
                )
                .order_by(DeletionRequest.accepted_at, DeletionRequest.id)
                .limit(limit)
            )
        ).all()
        accounts = conversations = 0
        for key, user_id in rows:
            if conversations >= limit:
                break
            if user_id is not None:
                locked = await self.db.scalar(
                    select(User.id).where(User.id == user_id).with_for_update(skip_locked=True)
                )
                if locked is None and await self.db.scalar(
                    select(User.id).where(User.id == user_id)
                ):
                    continue
            request = await self.db.scalar(
                select(DeletionRequest)
                .where(DeletionRequest.id == key)
                .with_for_update(skip_locked=True)
                .execution_options(populate_existing=True)
            )
            if request is None or request.status == "completed":
                continue
            if request.user_id is not None:
                conversations += await self._remove_conversations(
                    request.user_id, limit - conversations, expired=False
                )
                if await self.active_hold(request.user_id):
                    if request.status != "held":
                        await audit(
                            self.db,
                            self,
                            "privacy_delete_deferred",
                            "held",
                            request.id,
                            str(request.user_id),
                            actor=role,
                        )
                    request.status = "held"
                    continue
                remaining = await self.db.scalar(
                    select(
                        select(Conversation.id)
                        .where(Conversation.user_id == request.user_id)
                        .exists()
                    )
                )
                if remaining:
                    request.status = "accepted"
                    continue
                email = await self.db.scalar(
                    select(User.email_normalized).where(User.id == request.user_id)
                )
                await self.db.execute(
                    delete(Invitation).where(
                        or_(
                            Invitation.target_user_id == request.user_id,
                            Invitation.accepted_user_id == request.user_id,
                            Invitation.email_normalized == email,
                        )
                    )
                )
                await self.db.execute(delete(User).where(User.id == request.user_id))
                accounts += 1
                # FK SET NULL occurs server-side; keep the loaded object consistent.
                await self.db.refresh(request, attribute_names=["user_id"])
            request.status, request.completed_at = "completed", self.clock()
            await audit(
                self.db, self, "privacy_delete_completed", "success", request.id, actor=role
            )
            await self.db.flush()
        return accounts, conversations

    async def eligible_backlog(self, cutoff: datetime) -> bool:
        # Shared predicates for urgency and post-batch backlog prevent a full
        # identity batch from being silently deferred until the next daily run.
        return bool(
            await self.db.scalar(
                text("""SELECT
          EXISTS(SELECT FROM conversations c WHERE c.expires_at<=:cutoff
            AND NOT public.privacy_is_held(c.user_id,c.id))
          OR EXISTS(SELECT FROM auth_sessions s WHERE s.expires_at<=:cutoff
            AND NOT EXISTS(SELECT FROM privacy_holds h WHERE h.user_id=s.user_id
              AND h.scope='account' AND h.released_at IS NULL))
          OR EXISTS(SELECT FROM invitations i WHERE i.expires_at<=:cutoff
            AND NOT EXISTS(SELECT FROM privacy_holds h JOIN users u ON u.id=h.user_id
              WHERE h.released_at IS NULL AND h.scope='account' AND
                (u.id=i.target_user_id OR u.id=i.accepted_user_id
                  OR u.email_normalized=i.email_normalized)))
          OR EXISTS(SELECT FROM auth_rate_limits WHERE expires_at<=:cutoff)
          OR EXISTS(SELECT FROM auth_audit_events a
            WHERE a.occurred_at<=:cutoff-interval '90 days'
            AND NOT EXISTS(SELECT FROM privacy_holds h WHERE h.audit_subject=a.subject
                           AND h.released_at IS NULL))
          OR EXISTS(SELECT FROM privacy_holds WHERE released_at<=:cutoff-interval '90 days')
          OR EXISTS(SELECT FROM privacy_deletion_ledger WHERE expires_at<=:cutoff)
          OR EXISTS(SELECT FROM privacy_deletion_requests
            WHERE completed_at<=:cutoff-interval '90 days')"""),
                {"cutoff": cutoff},
            )
        )

    async def maintenance(self, limit: int = 100, *, force: bool = False) -> MaintenanceReport:
        role = await self.authorize("can_maintain")
        if not 1 <= limit <= 100:
            raise ValueError("Batch must be between 1 and 100")
        if not await self.db.scalar(
            text("SELECT pg_try_advisory_xact_lock(:key)"), {"key": MAINTENANCE_LOCK}
        ):
            return MaintenanceReport(status="busy")
        state = await self.db.get(MaintenanceState, 1, with_for_update=True)
        if state is None:
            raise AuthFailure(503, "service_unavailable")
        now = self.clock()
        overdue = int(
            await self.db.scalar(
                select(func.count())
                .select_from(PrivacyHold)
                .where(PrivacyHold.released_at.is_(None), PrivacyHold.review_due_at <= now)
            )
            or 0
        )
        overdue_requests = int(
            await self.db.scalar(
                select(func.count())
                .select_from(DeletionRequest)
                .where(
                    DeletionRequest.status != "completed", DeletionRequest.completion_due_at <= now
                )
            )
            or 0
        )
        report = MaintenanceReport(
            status="idle", overdue_holds=overdue, overdue_requests=overdue_requests
        )
        if overdue and (
            state.last_hold_alert_at is None or state.last_hold_alert_at <= now - timedelta(days=1)
        ):
            await audit(self.db, self, "privacy_holds_overdue", "attention", uuid4(), actor=role)
            state.last_hold_alert_at = now
        report.deadline_breached = await self.eligible_backlog(now - timedelta(hours=24))
        if report.deadline_breached:
            await audit(self.db, self, "privacy_purge_overdue", "attention", uuid4(), actor=role)
        daily = state.last_daily_at is None or state.last_daily_at < daily_target(now)
        urgent = await self.eligible_backlog(now - timedelta(hours=23))
        requests = bool(
            await self.db.scalar(select(exists().where(DeletionRequest.status != "completed")))
        )
        if force or daily or urgent or requests:
            report.accounts, report.conversations = await self._complete_requests(limit, role)
            owners = (
                await self.db.scalars(
                    select(Conversation.user_id)
                    .where(
                        Conversation.expires_at <= now,
                        ~func.public.privacy_is_held(Conversation.user_id, Conversation.id),
                    )
                    .distinct()
                    .order_by(Conversation.user_id)
                    .limit(limit)
                )
            ).all()
            for owner in owners:
                if report.conversations >= limit:
                    break
                if (
                    await self.db.scalar(
                        select(User.id).where(User.id == owner).with_for_update(skip_locked=True)
                    )
                    is not None
                ):
                    report.conversations += await self._remove_conversations(
                        owner, limit - report.conversations, expired=True
                    )
            # Bound each identity/metadata category; held rows are excluded by SQL,
            # while database delete triggers provide defense against bypass paths.
            account_hold = select(PrivacyHold.user_id).where(
                PrivacyHold.scope == "account", PrivacyHold.released_at.is_(None)
            )
            family_ids = (
                select(AuthSession.id)
                .where(AuthSession.expires_at <= now, AuthSession.user_id.not_in(account_hold))
                .limit(limit)
            )
            await self.db.execute(delete(AuthSession).where(AuthSession.id.in_(family_ids)))
            held_users = select(User.id).where(User.id.in_(account_hold))
            invitation_ids = (
                select(Invitation.id)
                .where(
                    Invitation.expires_at <= now,
                    or_(
                        Invitation.target_user_id.is_(None),
                        Invitation.target_user_id.not_in(held_users),
                    ),
                    or_(
                        Invitation.accepted_user_id.is_(None),
                        Invitation.accepted_user_id.not_in(held_users),
                    ),
                    Invitation.email_normalized.not_in(
                        select(User.email_normalized).where(User.id.in_(account_hold))
                    ),
                )
                .limit(limit)
            )
            await self.db.execute(delete(Invitation).where(Invitation.id.in_(invitation_ids)))
            rate_keys = (
                select(AuthRateLimit.dimension, AuthRateLimit.identifier, AuthRateLimit.window)
                .where(AuthRateLimit.expires_at <= now)
                .limit(limit)
            )
            await self.db.execute(
                delete(AuthRateLimit).where(
                    tuple_(
                        AuthRateLimit.dimension, AuthRateLimit.identifier, AuthRateLimit.window
                    ).in_(rate_keys)
                )
            )
            held_subjects = select(PrivacyHold.audit_subject).where(
                PrivacyHold.released_at.is_(None)
            )
            audit_ids = (
                select(AuthAudit.id)
                .where(
                    AuthAudit.occurred_at <= now - timedelta(days=90),
                    or_(AuthAudit.subject.is_(None), AuthAudit.subject.not_in(held_subjects)),
                )
                .limit(limit)
            )
            await self.db.execute(delete(AuthAudit).where(AuthAudit.id.in_(audit_ids)))
            await self.db.execute(
                delete(PrivacyHold).where(
                    PrivacyHold.id.in_(
                        select(PrivacyHold.id)
                        .where(PrivacyHold.released_at <= now - timedelta(days=90))
                        .limit(limit)
                    )
                )
            )
            ledger_keys = (
                select(DeletionLedger.kind, DeletionLedger.target_id)
                .where(DeletionLedger.expires_at <= now)
                .limit(limit)
            )
            await self.db.execute(
                delete(DeletionLedger).where(
                    tuple_(DeletionLedger.kind, DeletionLedger.target_id).in_(ledger_keys)
                )
            )
            await self.db.execute(
                delete(DeletionRequest).where(
                    DeletionRequest.id.in_(
                        select(DeletionRequest.id)
                        .where(DeletionRequest.completed_at <= now - timedelta(days=90))
                        .limit(limit)
                    )
                )
            )
            report.status = "completed"
            # Count only eligible (unheld) expired rows; holds are not a purge failure.
            report.backlog = await self.eligible_backlog(now)
            if not report.backlog:
                report.backlog = bool(
                    await self.db.scalar(
                        text("""SELECT EXISTS(
                    SELECT FROM privacy_deletion_requests r WHERE r.status='accepted'
                    AND NOT EXISTS(SELECT FROM privacy_holds h WHERE h.user_id=r.user_id
                                   AND h.released_at IS NULL))""")
                    )
                )
            if daily and not report.backlog:
                state.last_daily_at = now
            state.last_success_at = now
            await audit(self.db, self, "privacy_maintenance", "success", uuid4(), actor=role)
        if (
            report.backlog
            or report.deadline_breached
            or report.overdue_holds
            or report.overdue_requests
        ):
            report.status = "attention"
        return report
