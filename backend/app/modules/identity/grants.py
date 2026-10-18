"""Explicit existing-role grants; never create logins/passwords or run on startup."""

import argparse
import asyncio
import re
import sys

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool

from app.db.migrate import MigrationSettings
from app.db.session import protect_engine_logging

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


async def grant(runtime: str, operator: str, maintenance: str) -> None:
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
    finally:
        await engine.dispose()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime-role", required=True)
    parser.add_argument("--operator-role", required=True)
    parser.add_argument("--maintenance-role", required=True)
    args = parser.parse_args()
    try:
        asyncio.run(grant(args.runtime_role, args.operator_role, args.maintenance_role))
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
