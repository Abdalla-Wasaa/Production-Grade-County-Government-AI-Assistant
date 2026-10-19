"""Real PostgreSQL 17 migration, readiness, privilege and session acceptance."""

import asyncio
import json
from types import SimpleNamespace

import anyio
import psycopg
import pytest
from fastapi.testclient import TestClient
from psycopg import sql
from pydantic import SecretStr
from sqlalchemy import text
from sqlalchemy.engine import make_url

from app.core.config import Settings
from app.db.readiness import is_ready
from app.db.session import Database, get_session
from app.main import create_app

pytestmark = pytest.mark.integration


def settings(target, **kwargs):
    return Settings(environment="test", database_url=SecretStr(target.runtime), **kwargs)


def initialize(target):
    result = target.migrate()
    assert result.returncode == 0, result.stderr
    target.grant_revision()


def assert_unavailable(client):
    response = client.get("/health/ready")
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "service_unavailable"
    assert response.headers["Cache-Control"] == "no-store"
    assert client.get("/health/live").status_code == 200
    return response


def test_baseline_repeat_schema_and_readiness(target):
    with TestClient(create_app(settings(target))) as client:
        assert_unavailable(client)
        initialize(target)
        assert target.migrate().returncode == 0
        assert target.migrate("check").returncode == 0
        assert client.get("/health/ready").status_code == 200
        with psycopg.connect(target.admin) as db:
            names = {
                row[0]
                for row in db.execute(
                    "SELECT tablename FROM pg_tables WHERE schemaname='public'"
                ).fetchall()
            }
            assert names == {
                "alembic_version",
                "conversations",
                "messages",
                "users",
                "invitations",
                "auth_sessions",
                "refresh_tokens",
                "auth_audit_events",
                "auth_rate_limits",
                "privacy_operators",
                "privacy_holds",
                "privacy_deletion_requests",
                "privacy_deletion_ledger",
                "privacy_maintenance_state",
            }
            assert db.execute("SELECT version_num FROM public.alembic_version").fetchall() == [
                ("0006_privacy_lifecycle",)
            ]


@pytest.mark.parametrize("revisions", [[], ["0000_stale"], ["unknown"], ["0001_baseline", "extra"]])
def test_bad_revisions_and_recovery(target, revisions):
    initialize(target)
    with psycopg.connect(target.admin, autocommit=True) as db:
        db.execute("DELETE FROM public.alembic_version")
        for revision in revisions:
            db.execute("INSERT INTO public.alembic_version VALUES (%s)", (revision,))
    with TestClient(create_app(settings(target))) as client:
        assert_unavailable(client)
        assert target.migrate("check").returncode == 1
        with psycopg.connect(target.admin, autocommit=True) as db:
            db.execute("DELETE FROM public.alembic_version")
            db.execute("INSERT INTO public.alembic_version VALUES ('0006_privacy_lifecycle')")
        assert client.get("/health/ready").status_code == 200


def test_credentials_permissions_and_safe_logs(target, capsys):
    initialize(target)
    bad = (
        make_url(target.runtime)
        .set(password="wrong-synthetic-password")
        .render_as_string(hide_password=False)
    )
    with TestClient(
        create_app(Settings(environment="test", database_url=SecretStr(bad)))
    ) as client:
        response = assert_unavailable(client)
    with psycopg.connect(target.admin, autocommit=True) as db:
        db.execute(
            sql.SQL("REVOKE SELECT ON public.alembic_version FROM {}").format(
                sql.Identifier(make_url(target.runtime).username)
            )
        )
    with TestClient(create_app(settings(target))) as client:
        assert_unavailable(client)
        target.grant_revision()
        assert client.get("/health/ready").status_code == 200
    with psycopg.connect(
        target.runtime.replace("postgresql+psycopg:", "postgresql:"), autocommit=True
    ) as db:
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            db.execute("CREATE TABLE forbidden (id integer)")
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            db.execute("UPDATE public.alembic_version SET version_num='bad'")
    output = capsys.readouterr().err + response.text
    for sensitive in [
        "wrong-synthetic-password",
        make_url(target.runtime).password,
        target.name,
        "127.0.0.1",
        "0001_baseline",
        "SELECT",
    ]:
        assert sensitive not in output
    for line in output.splitlines()[:-1]:
        if line.startswith("{"):
            json.loads(line)


def test_unavailable_and_recovery(target):
    initialize(target)
    url = make_url(target.admin)
    # Disable connections to our newly created disposable database only.
    admin = url.set(database="postgres").render_as_string(hide_password=False)
    with psycopg.connect(admin, autocommit=True) as control:
        control.execute(
            sql.SQL("ALTER DATABASE {} ALLOW_CONNECTIONS false").format(sql.Identifier(target.name))
        )
        try:
            with TestClient(create_app(settings(target))) as client:
                assert_unavailable(client)
                control.execute(
                    sql.SQL("ALTER DATABASE {} ALLOW_CONNECTIONS true").format(
                        sql.Identifier(target.name)
                    )
                )
                assert client.get("/health/ready").status_code == 200
        finally:
            control.execute(
                sql.SQL("ALTER DATABASE {} ALLOW_CONNECTIONS true").format(
                    sql.Identifier(target.name)
                )
            )


def test_query_deadline_and_cleanup(target):
    initialize(target)
    with psycopg.connect(target.admin) as blocker:
        blocker.execute("LOCK TABLE public.alembic_version IN ACCESS EXCLUSIVE MODE")
        with TestClient(create_app(settings(target, db_readiness_timeout_seconds=0.15))) as client:
            import time

            start = time.monotonic()
            assert_unavailable(client)
            assert time.monotonic() - start < 2
            blocker.rollback()
            assert client.get("/health/ready").status_code == 200
            assert client.app.state.database.engine.pool.checkedout() == 0


async def test_sessions_rollback_isolation_cancellation_and_disposal(target):
    initialize(target)
    database = Database(settings(target))
    # Infrastructure-only scratch table in a disposable database, never a migration.
    with psycopg.connect(target.admin, autocommit=True) as db:
        db.execute("CREATE TABLE scratch (id integer)")
        db.execute(
            sql.SQL("GRANT SELECT, INSERT ON scratch TO {}").format(
                sql.Identifier(make_url(target.runtime).username)
            )
        )
    request = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(database=database)))
    dependency = get_session(request)
    first = await anext(dependency)
    second = database.sessions()
    assert first is not second
    await first.execute(text("INSERT INTO scratch VALUES (1)"))
    assert (await second.execute(text("SELECT count(*) FROM scratch"))).scalar_one() == 0
    await second.close()
    await dependency.aclose()
    async with database.sessions() as verify:
        assert (await verify.execute(text("SELECT count(*) FROM scratch"))).scalar_one() == 0

    async def cancelled_task():
        generator = get_session(request)
        session = await anext(generator)
        try:
            await session.execute(text("INSERT INTO scratch VALUES (2)"))
            await anyio.sleep_forever()
        finally:
            await generator.aclose()

    async with anyio.create_task_group() as group:
        group.start_soon(cancelled_task)
        await anyio.sleep(0.1)
        group.cancel_scope.cancel()
    assert database.engine.pool.checkedout() == 0
    old_pool = database.engine.pool
    await database.dispose()
    assert database.engine.pool is not old_pool
    with psycopg.connect(target.admin) as db:
        assert db.execute("SELECT count(*) FROM scratch").fetchone()[0] == 0


async def test_pool_checkout_deadline(target):
    initialize(target)
    database = Database(settings(target, db_pool_size=1, db_max_overflow=0))
    try:
        async with database.engine.connect():
            start = asyncio.get_running_loop().time()
            assert not await is_ready(database, 0.05)
            assert asyncio.get_running_loop().time() - start < 0.5
        assert await is_ready(database, 1)
        assert database.engine.pool.checkedout() == 0
    finally:
        await database.dispose()


def test_migration_failure_safe(target):
    target.migration = (
        make_url(target.migration)
        .set(password="bad-migration-secret")
        .render_as_string(hide_password=False)
    )
    result = target.migrate()
    assert result.returncode == 1
    assert "bad-migration-secret" not in result.stderr
    assert target.name not in result.stderr
    assert "Traceback" not in result.stderr


def test_connection_handshake_deadline(target):
    """A TCP peer that never answers must not consume the full driver timeout."""
    import socket
    import threading
    import time

    stop = threading.Event()
    listener = socket.socket()
    listener.bind(("127.0.0.1", 0))
    listener.listen()
    listener.settimeout(2)

    def stall():
        try:
            connection, _ = listener.accept()
            with connection:
                stop.wait(3)
        except OSError:
            pass

    thread = threading.Thread(target=stall, daemon=True)
    thread.start()
    url = (
        make_url(target.runtime)
        .set(port=listener.getsockname()[1])
        .render_as_string(hide_password=False)
    )
    try:
        config = Settings(
            environment="test", database_url=SecretStr(url), db_readiness_timeout_seconds=0.15
        )
        with TestClient(create_app(config)) as client:
            start = time.monotonic()
            assert_unavailable(client)
            assert time.monotonic() - start < 1.5
    finally:
        stop.set()
        listener.close()
        thread.join(timeout=3)
