"""Explicit synthetic operator tasks; token output is an exclusive 0600 file only."""

import argparse
import asyncio
import os
import stat
import sys
from datetime import timedelta
from pathlib import Path
from uuid import UUID, uuid4

from pydantic import SecretStr
from sqlalchemy import delete, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import validate_database_url
from app.db.session import protect_engine_logging
from app.modules.identity.models import AuthAudit, AuthRateLimit, AuthSession, Invitation, User
from app.modules.identity.repository import audit, lock_user, revoke_all
from app.modules.identity.schemas import Login
from app.modules.identity.security import AuthFailure, Tokens, digest, random_token
from app.modules.identity.settings import AuthSettings


def token_file(path: Path, raw: str) -> None:
    # Require an ignored local-only destination and private, non-symlink ancestors.
    destination = Path(os.path.abspath(path))
    if ".local" not in destination.parts:
        raise ValueError("Token destination must be under .local")
    for parent in reversed(destination.parents):
        if parent.is_symlink():
            raise ValueError("Symlink token directory")
    destination.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    info = destination.parent.stat()
    if info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) != 0o700:
        raise ValueError("Token directory must be owned and mode 0700")
    descriptor = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "w") as stream:
            stream.write(raw + "\n")
            stream.flush()
            os.fsync(stream.fileno())
    except BaseException:
        destination.unlink(missing_ok=True)
        raise


async def issue(
    db: AsyncSession,
    tokens: Tokens,
    *,
    email: str,
    role: str,
    language: str,
    operator: str,
    reset: bool = False,
) -> str:
    normalized = Login.email_format(email)
    if role not in {"citizen", "staff", "admin"} or language not in {"en", "sw"}:
        raise ValueError("Invalid invitation parameters")
    # Serialize reissuance even if no invitation row exists yet.
    lock_key = int(tokens.pseudonym(normalized)[:15], 16)
    await db.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": lock_key})
    user = (
        await db.execute(select(User).where(User.email_normalized == normalized).with_for_update())
    ).scalar_one_or_none()
    if (reset and (user is None or user.status != "active")) or (not reset and user is not None):
        raise ValueError("Account is not eligible")
    purpose = "password_reset" if reset else "activation"
    now = tokens.clock()
    await db.execute(
        update(Invitation)
        .where(
            Invitation.email_normalized == normalized,
            Invitation.purpose == purpose,
            Invitation.consumed_at.is_(None),
            Invitation.revoked_at.is_(None),
        )
        .values(revoked_at=now)
    )
    raw = random_token()
    db.add(
        Invitation(
            id=uuid4(),
            email_normalized=normalized,
            purpose=purpose,
            target_user_id=user.id if user else None,
            role=user.role if user else role,
            preferred_language=user.preferred_language if user else language,
            privacy_notice_version=tokens.config.privacy_notice_version,
            token_digest=digest(raw),
            issuer=tokens.pseudonym(operator),
            created_at=now,
            expires_at=now + timedelta(hours=24),
        )
    )
    await audit(
        db,
        tokens,
        "reset_issue" if reset else "invitation_issue",
        "success",
        uuid4(),
        str(user.id) if user else normalized,
    )
    return raw


async def run(args: argparse.Namespace) -> None:
    config = AuthSettings()
    tokens = Tokens(config)
    secret = SecretStr(os.environ["COUNTY_AUTH_OPERATOR_DATABASE_URL"])
    validate_database_url(secret)
    engine = create_async_engine(
        secret.get_secret_value(),
        poolclass=NullPool,
        hide_parameters=True,
        connect_args={"connect_timeout": 5},
    )
    protect_engine_logging(engine)
    created_file = False
    try:
        async with (
            asyncio.timeout(30),
            async_sessionmaker(engine, expire_on_commit=False)() as db,
            db.begin(),
        ):
            if args.command in {"invite", "recover"}:
                raw = await issue(
                    db,
                    tokens,
                    email=args.email,
                    role=args.role,
                    language=args.language,
                    operator=args.operator,
                    reset=args.command == "recover",
                )
                token_file(args.output, raw)
                created_file = True
            elif args.command == "revoke-invitation":
                invitation = (
                    await db.execute(
                        select(Invitation).where(Invitation.id == args.id).with_for_update()
                    )
                ).scalar_one_or_none()
                if invitation is None:
                    raise ValueError("Invitation unavailable")
                invitation.revoked_at = tokens.clock()
                await audit(db, tokens, "invitation_revoke", "success", uuid4(), str(invitation.id))
            elif args.command in {"disable", "set-role"}:
                user = await lock_user(db, args.id)
                if user is None:
                    raise ValueError("Account unavailable")
                await revoke_all(db, user, tokens, args.command)
                if args.command == "disable":
                    user.status = "disabled"
                else:
                    user.role = args.role
                await audit(
                    db,
                    tokens,
                    "account_disable" if args.command == "disable" else "role_change",
                    "success",
                    uuid4(),
                    str(user.id),
                )
            elif args.command == "purge":
                now = tokens.clock()
                # Family cascade deletes retained token history only after expiry+24h.
                await db.execute(
                    delete(AuthSession).where(AuthSession.expires_at < now - timedelta(hours=24))
                )
                await db.execute(
                    delete(Invitation).where(Invitation.expires_at < now - timedelta(hours=24))
                )
                await db.execute(delete(AuthRateLimit).where(AuthRateLimit.expires_at < now))
                # Audit retention requires separate controlled role/incident-hold check.
                if not args.no_incident_hold:
                    raise ValueError("Retention requires explicit incident-hold verification")
                await db.execute(
                    delete(AuthAudit).where(AuthAudit.occurred_at < now - timedelta(days=90))
                )
                await audit(db, tokens, "retention_purge", "success", uuid4())
    except BaseException:
        if created_file:
            args.output.unlink(missing_ok=True)
        raise
    finally:
        await engine.dispose()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Synthetic identity operator; never pass credentials/tokens as arguments"
    )
    parser.add_argument(
        "command",
        choices=["invite", "recover", "revoke-invitation", "disable", "set-role", "purge"],
    )
    parser.add_argument("--email")
    parser.add_argument("--role", choices=["citizen", "staff", "admin"], default="citizen")
    parser.add_argument("--language", choices=["en", "sw"], default="en")
    parser.add_argument("--operator", required=True, help="Nonpersonal operator pseudonym")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--id", type=UUID)
    parser.add_argument("--no-incident-hold", action="store_true")
    args = parser.parse_args()
    if args.command in {"invite", "recover"} and (not args.output or not args.email):
        parser.error("invite/recover require --email and --output")
    if args.command in {"revoke-invitation", "disable", "set-role"} and not args.id:
        parser.error("command requires --id")
    try:
        asyncio.run(run(args))
    except (Exception, AuthFailure):
        print(
            "Identity operator operation failed; no token or credential is printed.",
            file=sys.stderr,
        )
        return 1
    print(
        "Identity operator operation completed; inspect the private handoff file where applicable."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
