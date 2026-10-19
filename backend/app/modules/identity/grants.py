"""Explicit existing-role grants; never create logins/passwords or run on startup."""

import argparse
import asyncio
import base64
import hashlib
import re
import sys
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool

from app.db.migrate import MigrationSettings
from app.db.session import protect_engine_logging
from app.modules.privacy.settings import private_value

RUNTIME_GRANTS = (
    "SELECT, INSERT ON users",
    "UPDATE(password_hash,preferred_language,privacy_notice_version,"
    "privacy_notice_acknowledged_at,token_version,updated_at) ON users",
    "SELECT ON invitations",
    "UPDATE(consumed_at,accepted_user_id) ON invitations",
    "SELECT, INSERT, UPDATE ON auth_sessions,refresh_tokens,auth_rate_limits",
    "INSERT ON auth_audit_events",
    "SELECT ON alembic_version",
    "SELECT, INSERT, DELETE ON conversations",
    "UPDATE(title,language,next_sequence,version,last_activity_at,updated_at,expires_at) "
    "ON conversations",
    "SELECT, INSERT ON messages",
    "EXECUTE ON FUNCTION public.privacy_is_held(UUID,UUID)",
    "EXECUTE ON FUNCTION public.privacy_audit_key_matches(TEXT)",
)
OPERATOR_GRANTS = (
    "SELECT ON users",
    "UPDATE(role,status,token_version,updated_at) ON users",
    "SELECT, INSERT ON invitations",
    "UPDATE(revoked_at) ON invitations",
    "UPDATE(token_version,updated_at) ON users",
    "SELECT ON auth_sessions",
    "UPDATE(revoked_at,reason) ON auth_sessions",
    "INSERT ON auth_audit_events",
)
MAINTENANCE_GRANTS = (
    "SELECT, DELETE ON invitations,auth_sessions,auth_rate_limits,auth_audit_events",
    "INSERT ON auth_audit_events",
)


PRIVACY_OPERATOR_GRANTS = (
    "SELECT ON privacy_operators,privacy_maintenance_state,privacy_holds,privacy_deletion_requests",
    "SELECT(id,user_id) ON conversations",
    "INSERT,UPDATE ON privacy_holds",
    "INSERT ON privacy_deletion_requests",
)
PRIVACY_MAINTENANCE_GRANTS = (
    "SELECT ON privacy_operators,privacy_maintenance_state,privacy_holds,privacy_deletion_requests",
    "UPDATE ON privacy_maintenance_state",
    "UPDATE(status,completed_at) ON privacy_deletion_requests",
    "DELETE ON privacy_holds,privacy_deletion_requests,privacy_deletion_ledger",
    "SELECT ON privacy_deletion_ledger",
    "SELECT(id,status,email_normalized) ON users",
    "UPDATE(updated_at) ON users",
    "DELETE ON users",
    "SELECT(id,user_id,expires_at) ON conversations",
    "UPDATE(updated_at) ON conversations",
    "DELETE ON conversations",
    "EXECUTE ON FUNCTION public.privacy_is_held(UUID,UUID)",
)


async def grant(
    runtime: str, operator: str, maintenance: str, privacy_key: bytes | None = None
) -> None:
    roles = (runtime, operator, maintenance)
    if len(set(roles)) != 3 or any(
        not re.fullmatch(r"[a-z][a-z0-9_]{0,62}", role) for role in roles
    ):
        raise ValueError("Distinct unprivileged role names required")
    settings = MigrationSettings()
    engine = create_async_engine(
        settings.migration_database_url.get_secret_value(), poolclass=NullPool, hide_parameters=True
    )
    protect_engine_logging(engine)
    try:
        async with asyncio.timeout(15), engine.begin() as connection:
            for role, statements in zip(
                roles, (RUNTIME_GRANTS, OPERATOR_GRANTS, MAINTENANCE_GRANTS), strict=True
            ):
                flags = (
                    await connection.execute(
                        text(
                            "SELECT rolsuper,rolcreaterole,rolcreatedb,rolreplication,rolbypassrls "
                            "FROM pg_roles WHERE rolname=:role"
                        ),
                        {"role": role},
                    )
                ).one_or_none()
                if flags is None or any(flags):
                    raise ValueError("Role absent or privileged")
                inherited = await connection.scalar(
                    text(
                        "SELECT EXISTS(SELECT FROM pg_auth_members m JOIN pg_roles r "
                        "ON r.oid=m.member WHERE r.rolname=:role) OR EXISTS("
                        "SELECT FROM pg_class c JOIN pg_roles r ON r.oid=c.relowner "
                        "WHERE r.rolname=:role) OR EXISTS(SELECT FROM pg_database d "
                        "JOIN pg_roles r ON r.oid=d.datdba WHERE r.rolname=:role)"
                    ),
                    {"role": role},
                )
                if inherited:
                    raise ValueError("Role must not inherit privileges or own database objects")
                # Name validated above; SQL identifiers cannot be bound as values.
                database = connection.engine.url.database
                if database is None:
                    raise ValueError("Database required")
                quoted_database = '"' + database.replace('"', '""') + '"'
                await connection.execute(
                    text(f'GRANT CONNECT ON DATABASE {quoted_database} TO "{role}"')
                )
                await connection.execute(text(f'GRANT USAGE ON SCHEMA public TO "{role}"'))
                for statement in statements:
                    await connection.execute(text(f'GRANT {statement} TO "{role}"'))
            if privacy_key is not None:
                if len(privacy_key) < 32 or len(set(privacy_key)) < 16:
                    raise ValueError("Invalid privacy audit key")
                fingerprint = hashlib.sha256(privacy_key).hexdigest()
                matched = await connection.scalar(
                    text("""UPDATE privacy_maintenance_state
                    SET audit_key_sha256=:key WHERE id=1
                    AND (audit_key_sha256 IS NULL OR audit_key_sha256=:key) RETURNING id"""),
                    {"key": fingerprint},
                )
                if matched is None:
                    raise ValueError("Audit key change requires a reviewed migration")
                for role, hold, request, maintain, grants in (
                    (operator, True, True, False, PRIVACY_OPERATOR_GRANTS),
                    (maintenance, False, False, True, PRIVACY_MAINTENANCE_GRANTS),
                ):
                    for statement in grants:
                        await connection.execute(text(f'GRANT {statement} TO "{role}"'))
                    await connection.execute(
                        text("""INSERT INTO privacy_operators
                        (role_name,enabled,can_hold,can_request,can_maintain)
                        VALUES(:role,true,:hold,:request,:maintain) ON CONFLICT(role_name)
                        DO UPDATE SET enabled=true,can_hold=:hold,can_request=:request,
                                      can_maintain=:maintain"""),
                        {"role": role, "hold": hold, "request": request, "maintain": maintain},
                    )
                    await connection.execute(
                        text("""INSERT INTO auth_audit_events
                        (id,occurred_at,actor,subject,action,outcome,request_id)
                        VALUES(gen_random_uuid(),clock_timestamp(),
                          encode(sha256(convert_to(session_user::text,'UTF8')),'hex'),
                          encode(sha256(convert_to(:role,'UTF8')),'hex'),
                          'privacy_role_grant','success',gen_random_uuid())"""),
                        {"role": role},
                    )

    finally:
        await engine.dispose()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime-role", required=True)
    parser.add_argument("--operator-role", required=True)
    parser.add_argument("--maintenance-role", required=True)
    parser.add_argument("--privacy-audit-key-file", type=Path)
    args = parser.parse_args()
    try:
        key = (
            base64.b64decode(private_value(args.privacy_audit_key_file), validate=True)
            if args.privacy_audit_key_file
            else None
        )
        asyncio.run(grant(args.runtime_role, args.operator_role, args.maintenance_role, key))
    except Exception:
        print(
            "Identity grant operation failed; review role setup without printing credentials.",
            file=sys.stderr,
        )
        return 1
    print("Identity role grants completed; verify privileges before use.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
