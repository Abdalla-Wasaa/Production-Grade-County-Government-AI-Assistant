"""Explicit opt-in; fresh random databases and roles only, never reset existing DBs."""

import os
import secrets
import subprocess
import sys
from dataclasses import dataclass
from uuid import uuid4

import psycopg
import pytest
from psycopg import sql
from sqlalchemy.engine import make_url


@dataclass
class Target:
    admin: str
    migration: str
    runtime: str
    name: str

    def migrate(self, operation="upgrade"):
        environment = {k: v for k, v in os.environ.items() if not k.startswith("COUNTY_")}
        environment["COUNTY_MIGRATION_DATABASE_URL"] = self.migration
        return subprocess.run(
            [sys.executable, "-m", "app.db.migrate", operation],
            env=environment,
            text=True,
            capture_output=True,
        )

    def grant_revision(self):
        with psycopg.connect(self.admin, autocommit=True) as connection:
            connection.execute(
                sql.SQL("GRANT SELECT ON public.alembic_version TO {}").format(
                    sql.Identifier(make_url(self.runtime).username)
                )
            )

    def grant_auth(self):
        role = sql.Identifier(make_url(self.runtime).username)
        statements = [
            "GRANT SELECT, INSERT ON users TO {}",
            "GRANT UPDATE(password_hash,preferred_language,privacy_notice_version,"
            "privacy_notice_acknowledged_at,token_version,updated_at) ON users TO {}",
            "GRANT SELECT ON invitations TO {}",
            "GRANT UPDATE(consumed_at,accepted_user_id) ON invitations TO {}",
            "GRANT SELECT, INSERT, UPDATE ON auth_sessions,refresh_tokens,auth_rate_limits TO {}",
            "GRANT INSERT ON auth_audit_events TO {}",
            "GRANT EXECUTE ON FUNCTION public.privacy_is_held(UUID,UUID) TO {}",
            "GRANT EXECUTE ON FUNCTION public.privacy_audit_key_matches(TEXT) TO {}",
        ]
        with psycopg.connect(self.admin, autocommit=True) as connection:
            for statement in statements:
                connection.execute(sql.SQL(statement).format(role))


@pytest.fixture
def target():
    raw = os.environ.get("COUNTY_TEST_ADMIN_URL")
    if not raw:
        pytest.skip("set COUNTY_TEST_ADMIN_URL and COUNTY_TEST_DISPOSABLE=YES for integration")
    if os.environ.get("COUNTY_TEST_DISPOSABLE") != "YES":
        pytest.fail("Disposable database authorization required")
    url = make_url(raw)
    if (
        url.drivername != "postgresql+psycopg"
        or url.host not in {"localhost", "127.0.0.1"}
        or url.database != "postgres"
        or url.query
    ):
        pytest.fail("Integration admin must target loopback postgres database without options")
    admin = url.set(drivername="postgresql").render_as_string(hide_password=False)
    name = "county_test_" + uuid4().hex
    migrator, runtime = name + "_m", name + "_r"
    password = secrets.token_urlsafe(24)
    created_roles = []
    created_db = False
    with psycopg.connect(admin, autocommit=True) as connection:
        assert 170000 <= connection.info.server_version < 180000, "PostgreSQL 17 required"
        try:
            for role in [migrator, runtime]:
                connection.execute(
                    sql.SQL("CREATE ROLE {} LOGIN PASSWORD {}").format(
                        sql.Identifier(role), sql.Literal(password)
                    )
                )
                created_roles.append(role)
            connection.execute(
                sql.SQL("CREATE DATABASE {} OWNER {}").format(
                    sql.Identifier(name), sql.Identifier(migrator)
                )
            )
            created_db = True
            connection.execute(
                sql.SQL("REVOKE ALL ON DATABASE {} FROM PUBLIC").format(sql.Identifier(name))
            )
            connection.execute(
                sql.SQL("GRANT CONNECT ON DATABASE {} TO {}").format(
                    sql.Identifier(name), sql.Identifier(runtime)
                )
            )
            db_admin = url.set(drivername="postgresql", database=name).render_as_string(
                hide_password=False
            )
            with psycopg.connect(db_admin, autocommit=True) as db:
                db.execute("REVOKE ALL ON SCHEMA public FROM PUBLIC")
                db.execute(
                    sql.SQL("GRANT USAGE ON SCHEMA public TO {}").format(sql.Identifier(runtime))
                )

            def role_url(role):
                return url.set(database=name, username=role, password=password).render_as_string(
                    hide_password=False
                )

            yield Target(db_admin, role_url(migrator), role_url(runtime), name)
        finally:
            # Only resources created successfully by this fixture can be removed.
            assert name.startswith("county_test_") and len(name) == 44
            if created_db:
                connection.execute(
                    sql.SQL("DROP DATABASE {} WITH (FORCE)").format(sql.Identifier(name))
                )
            for role in reversed(created_roles):
                connection.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(role)))
