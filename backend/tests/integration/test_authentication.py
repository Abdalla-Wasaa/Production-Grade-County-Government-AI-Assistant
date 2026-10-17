"""Actual PostgreSQL HTTP security acceptance; requires disposable target opt-in."""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from uuid import UUID, uuid4

import psycopg
import pytest
from auth_helpers import auth_settings
from fastapi.testclient import TestClient
from pydantic import SecretStr
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import Settings
from app.db.session import protect_engine_logging
from app.main import create_app
from app.modules.identity.operator import issue
from app.modules.identity.security import Tokens, digest

pytestmark = pytest.mark.integration
ORIGIN = "http://127.0.0.1"
PASSWORD = "synthetic river valley passphrase 42"


@pytest.fixture
def auth(target, tmp_path, monkeypatch):
    config = auth_settings(tmp_path, monkeypatch)
    monkeypatch.setenv("COUNTY_AUTH_HASH_CONCURRENCY", "2")
    result = target.migrate()
    assert result.returncode == 0, "Identity migration failed"
    target.grant_revision()
    target.grant_auth()
    application = create_app(
        Settings(environment="test", auth_enabled=True, database_url=SecretStr(target.runtime))
    )
    with TestClient(application, base_url=ORIGIN) as client:
        yield target, client, config


def invitation(auth, email="pilot@example.invalid", reset=False):
    target, _client, config = auth

    async def create():
        engine = create_async_engine(
            make_url(target.admin).set(drivername="postgresql+psycopg"), hide_parameters=True
        )
        protect_engine_logging(engine)
        try:
            async with async_sessionmaker(engine)() as db, db.begin():
                return await issue(
                    db,
                    Tokens(config),
                    email=email,
                    role="citizen",
                    language="en",
                    operator="synthetic-test-operator",
                    reset=reset,
                )
        finally:
            await engine.dispose()

    return asyncio.run(create())


def csrf(client):
    result = client.get("/api/v1/auth/csrf", headers={"Origin": ORIGIN})
    assert result.status_code == 200
    return {"Origin": ORIGIN, "X-CSRF-Token": result.json()["csrf_token"]}


def activation(client, raw, **changes):
    return client.post(
        "/api/v1/auth/activate",
        headers=csrf(client),
        json={
            "token": raw,
            "password": PASSWORD,
            "preferred_language": "en",
            "privacy_notice_version": "synthetic-v1",
            "privacy_notice_acknowledged": True,
            **changes,
        },
    )


def login(client, email="pilot@example.invalid", password=PASSWORD):
    return client.post(
        "/api/v1/auth/login", headers=csrf(client), json={"email": email, "password": password}
    )


def account(auth, email="pilot@example.invalid"):
    target, client, _config = auth
    raw = invitation(auth, email)
    assert activation(client, raw).status_code == 204
    result = login(client, email)
    assert result.status_code == 200
    return result.json(), {"Authorization": "Bearer " + result.json()["access_token"]}


def test_activation_login_current_user_and_digest_only_storage(auth):
    target, client, _config = auth
    raw = invitation(auth)
    assert activation(client, raw).status_code == 204
    assert "county_refresh" not in client.cookies
    assert activation(client, raw).status_code == 400
    result = login(client)
    assert result.status_code == 200 and result.json()["expires_in"] == 900
    access = result.json()["access_token"]
    me = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer " + access})
    assert me.json() == result.json()["user"]
    assert me.headers["Cache-Control"] == "no-store"
    with psycopg.connect(target.admin) as db:
        row = db.execute("SELECT token_digest,consumed_at FROM invitations").fetchone()
        assert row[0] == digest(raw) and row[1]
        assert db.execute("SELECT password_hash FROM users").fetchone()[0].startswith("$argon2id$")
        assert db.execute("SELECT count(*) FROM auth_audit_events").fetchone()[0] >= 3
    cookie = result.headers["set-cookie"]
    assert "HttpOnly" in cookie and "SameSite=strict" in cookie and "Path=/api/v1/auth" in cookie


@pytest.mark.parametrize("state", ["expired", "revoked"])
def test_invalid_invitations_and_no_partial_user(auth, state):
    target, client, _config = auth
    raw = invitation(auth)
    with psycopg.connect(target.admin) as db:
        # Preserve valid timestamp ordering while making the invitation expired.
        if state == "expired":
            db.execute(
                "UPDATE invitations SET created_at=now()-interval '2 days', "
                "expires_at=now()-interval '1 day'"
            )
        else:
            db.execute("UPDATE invitations SET revoked_at=now()")
    assert activation(client, raw).status_code == 400
    with psycopg.connect(target.admin) as db:
        assert db.execute("SELECT count(*) FROM users").fetchone()[0] == 0


def test_parallel_activation_consumes_once(auth):
    target, client, _config = auth
    raw = invitation(auth)
    headers = csrf(client)
    headers["Cookie"] = "county_csrf=" + headers["X-CSRF-Token"]
    body = {
        "token": raw,
        "password": PASSWORD,
        "preferred_language": "en",
        "privacy_notice_version": "synthetic-v1",
        "privacy_notice_acknowledged": True,
    }
    with ThreadPoolExecutor(max_workers=2) as workers:
        results = list(
            workers.map(
                lambda _: client.post(
                    "/api/v1/auth/activate", headers=headers, json=body
                ).status_code,
                range(2),
            )
        )
    # Bounded hashing may reject overload; retry cannot create a second account.
    assert sorted(results) == [204, 400]
    assert activation(client, raw).status_code == 400
    with psycopg.connect(target.admin) as db:
        assert db.execute("SELECT count(*) FROM users").fetchone()[0] == 1


def test_rotation_reuse_commits_family_revocation(auth):
    target, client, _config = auth
    result, bearer = account(auth)
    old = client.cookies.get("county_refresh")
    headers = csrf(client)
    rotated = client.post("/api/v1/auth/refresh", headers=headers, json={})
    assert rotated.status_code == 200 and client.cookies.get("county_refresh") != old
    headers["Cookie"] = f"county_refresh={old}; county_csrf={headers['X-CSRF-Token']}"
    assert client.post("/api/v1/auth/refresh", headers=headers, json={}).status_code == 401
    assert client.get("/api/v1/auth/me", headers=bearer).status_code == 401
    with psycopg.connect(target.admin) as db:
        assert db.execute("SELECT reason FROM auth_sessions").fetchone()[0] == "refresh_reuse"
        assert db.execute("SELECT count(*) FROM refresh_tokens").fetchone()[0] == 2


def test_parallel_refresh_has_one_successor_and_revokes_on_replay(auth):
    target, client, _config = auth
    account(auth)
    raw = client.cookies.get("county_refresh")
    headers = csrf(client)
    headers["Cookie"] = f"county_refresh={raw}; county_csrf={headers['X-CSRF-Token']}"
    with ThreadPoolExecutor(max_workers=2) as workers:
        results = list(
            workers.map(
                lambda _: client.post("/api/v1/auth/refresh", headers=headers, json={}).status_code,
                range(2),
            )
        )
    assert sorted(results) == [200, 401]
    with psycopg.connect(target.admin) as db:
        assert db.execute("SELECT count(*) FROM refresh_tokens").fetchone()[0] == 2
        assert db.execute("SELECT revoked_at IS NOT NULL FROM auth_sessions").fetchone()[0]


@pytest.mark.parametrize(
    "headers",
    [{}, {"Origin": "null"}, {"Origin": "http://attacker.invalid", "X-CSRF-Token": "forged"}],
)
def test_csrf_rejects_before_login(auth, headers):
    _target, client, _config = auth
    result = client.post(
        "/api/v1/auth/login",
        headers=headers,
        json={"email": "pilot@example.invalid", "password": PASSWORD},
    )
    assert result.status_code == 403


def test_shared_failure_limits_and_audit(auth):
    target, client, _config = auth
    for _ in range(5):
        assert login(client, password="incorrect").status_code == 401
    result = login(client, password="incorrect")
    assert result.status_code == 429 and int(result.headers["Retry-After"]) > 0
    with psycopg.connect(target.admin) as db:
        assert (
            db.execute(
                "SELECT count FROM auth_rate_limits WHERE dimension='login_account'"
            ).fetchone()[0]
            >= 5
        )
        assert (
            db.execute("SELECT count(*) FROM auth_audit_events WHERE outcome='denied'").fetchone()[
                0
            ]
            >= 5
        )
    # New HTTP client using same application must observe the same DB counters.
    with TestClient(client.app, base_url=ORIGIN) as other:
        assert login(other, password="incorrect").status_code == 429


def test_logout_all_revocation_and_disabled_account(auth):
    target, client, _config = auth
    _result, bearer = account(auth)
    headers = {**csrf(client), **bearer}
    assert client.post("/api/v1/auth/logout-all", headers=headers, json={}).status_code == 204
    assert client.get("/api/v1/auth/me", headers=bearer).status_code == 401
    with psycopg.connect(target.admin) as db:
        db.execute("UPDATE users SET status='disabled'")
    assert login(client).status_code == 401


def test_own_session_listing_revoke_and_unknown_access(auth):
    _target, client, _config = auth
    _result, bearer = account(auth)
    listed = client.get("/api/v1/auth/sessions", headers=bearer)
    assert listed.status_code == 200 and len(listed.json()["items"]) == 1
    item = listed.json()["items"][0]
    assert item["is_current"] and "token_digest" not in item
    assert (
        client.delete(
            f"/api/v1/auth/sessions/{uuid4()}", headers={**csrf(client), **bearer}
        ).status_code
        == 404
    )
    assert (
        client.delete(
            f"/api/v1/auth/sessions/{item['id']}", headers={**csrf(client), **bearer}
        ).status_code
        == 204
    )
    assert client.get("/api/v1/auth/me", headers=bearer).status_code == 401


def test_operator_reset_revokes_sessions_and_rejects_replay(auth):
    _target, client, _config = auth
    _result, bearer = account(auth)
    raw = invitation(auth, reset=True)
    assert (
        activation(client, raw, password="a different synthetic passphrase 43").status_code == 204
    )
    assert client.get("/api/v1/auth/me", headers=bearer).status_code == 401
    assert activation(client, raw).status_code == 400
    assert login(client).status_code == 401
    assert login(client, password="a different synthetic passphrase 43").status_code == 200


def test_no_public_role_escalation_and_runtime_permissions(auth):
    target, client, _config = auth
    raw = invitation(auth)
    assert activation(client, raw, role="admin").status_code == 422
    result, _bearer = account(auth, email="second@example.invalid")
    assert result["user"]["role"] == "citizen"
    with psycopg.connect(
        target.runtime.replace("postgresql+psycopg:", "postgresql:"), autocommit=True
    ) as db:
        for statement in [
            "UPDATE users SET role='admin'",
            "UPDATE users SET status='active'",
            "DELETE FROM auth_audit_events",
            "UPDATE invitations SET issuer='forged'",
            "CREATE TABLE forbidden(id integer)",
            "UPDATE alembic_version SET version_num='bad'",
        ]:
            with pytest.raises(psycopg.errors.InsufficientPrivilege):
                db.execute(statement)


def test_other_user_session_is_concealed_even_from_admin_role(auth):
    target, client, _config = auth
    first, first_bearer = account(auth)
    _second, second_bearer = account(auth, email="other@example.invalid")
    second_session = client.get("/api/v1/auth/sessions", headers=second_bearer).json()["items"][0][
        "id"
    ]
    with psycopg.connect(target.admin) as db:
        db.execute("UPDATE users SET role='admin' WHERE id=%s", (first["user"]["id"],))
    listed = client.get("/api/v1/auth/sessions", headers=first_bearer)
    assert all(item["id"] != second_session for item in listed.json()["items"])
    denied = client.delete(
        f"/api/v1/auth/sessions/{second_session}", headers={**csrf(client), **first_bearer}
    )
    assert denied.status_code == 404
    assert client.get("/api/v1/auth/me", headers=first_bearer).json()["role"] == "admin"


def test_audit_failure_rolls_back_logout(auth):
    target, client, _config = auth
    _result, bearer = account(auth)
    role = make_url(target.runtime).username
    from psycopg import sql

    with psycopg.connect(target.admin, autocommit=True) as db:
        db.execute(
            sql.SQL("REVOKE INSERT ON auth_audit_events FROM {}").format(sql.Identifier(role))
        )
    result = client.post("/api/v1/auth/logout", headers=csrf(client), json={})
    assert result.status_code == 503
    with psycopg.connect(target.admin) as db:
        assert db.execute("SELECT revoked_at FROM auth_sessions").fetchone()[0] is None
    assert "Set-Cookie" not in result.headers
    assert client.get("/health/live").status_code == 200


def test_expired_family_and_logout_idempotency(auth):
    target, client, _config = auth
    _result, bearer = account(auth)
    with psycopg.connect(target.admin) as db:
        db.execute(
            "UPDATE auth_sessions SET created_at=now()-interval '8 days', "
            "expires_at=now()-interval '1 day'"
        )
    assert client.get("/api/v1/auth/me", headers=bearer).status_code == 401
    assert client.post("/api/v1/auth/refresh", headers=csrf(client), json={}).status_code == 401
    assert client.post("/api/v1/auth/logout", headers=csrf(client), json={}).status_code == 204
    assert client.post("/api/v1/auth/logout", headers=csrf(client), json={}).status_code == 204


def test_authentication_database_outage_and_recovery(auth):
    target, client, _config = auth
    _result, bearer = account(auth)
    from psycopg import sql

    control_url = (
        make_url(target.admin).set(database="postgres").render_as_string(hide_password=False)
    )
    with psycopg.connect(control_url, autocommit=True) as control:
        control.execute(
            sql.SQL("ALTER DATABASE {} ALLOW_CONNECTIONS false").format(sql.Identifier(target.name))
        )
        try:
            control.execute(
                "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname=%s",
                (target.name,),
            )
            result = client.get("/api/v1/auth/me", headers=bearer)
            assert result.status_code == 503
            assert result.json()["error"]["code"] == "service_unavailable"
            assert client.get("/health/live").status_code == 200
        finally:
            control.execute(
                sql.SQL("ALTER DATABASE {} ALLOW_CONNECTIONS true").format(
                    sql.Identifier(target.name)
                )
            )
    assert client.get("/api/v1/auth/me", headers=bearer).status_code == 200


def test_explicit_operator_and_maintenance_grants(target, tmp_path, monkeypatch):
    import argparse
    import secrets

    from psycopg import sql

    from app.modules.identity.grants import grant
    from app.modules.identity.operator import run

    config = auth_settings(tmp_path, monkeypatch)
    assert target.migrate().returncode == 0
    target.grant_revision()
    runtime = make_url(target.runtime).username
    op_role, maint_role = "p201_op_" + uuid4().hex, "p201_ret_" + uuid4().hex
    password = secrets.token_urlsafe(32)
    control_url = (
        make_url(target.admin).set(database="postgres").render_as_string(hide_password=False)
    )
    with psycopg.connect(control_url, autocommit=True) as control:
        try:
            for role in [op_role, maint_role]:
                control.execute(
                    sql.SQL("CREATE ROLE {} LOGIN PASSWORD {}").format(
                        sql.Identifier(role), sql.Literal(password)
                    )
                )
            monkeypatch.setenv("COUNTY_MIGRATION_DATABASE_URL", target.migration)
            asyncio.run(grant(runtime, op_role, maint_role))
            operator_url = (
                make_url(target.runtime)
                .set(username=op_role, password=password)
                .render_as_string(hide_password=False)
            )
            monkeypatch.setenv("COUNTY_AUTH_OPERATOR_DATABASE_URL", operator_url)
            output = tmp_path / ".local" / "identity" / "handoff"
            asyncio.run(
                run(
                    argparse.Namespace(
                        command="invite",
                        email="operator@example.invalid",
                        role="staff",
                        language="sw",
                        operator="synthetic-issuer",
                        output=output,
                    )
                )
            )
            assert len(output.read_text().strip()) == 43
            import os
            import subprocess
            import sys

            cli_output = output.parent / "cli-token"
            cli_environment = {
                key: value
                for key, value in os.environ.items()
                if key not in {"COUNTY_TEST_ADMIN_URL", "COUNTY_MIGRATION_DATABASE_URL"}
            }
            command = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "app.modules.identity.operator",
                    "invite",
                    "--email",
                    "cli@example.invalid",
                    "--operator",
                    "synthetic-cli-issuer",
                    "--output",
                    str(cli_output),
                ],
                cwd=Path(__file__).resolve().parents[2],
                env=cli_environment,
                capture_output=True,
                text=True,
                timeout=30,
            )
            assert command.returncode == 0
            assert cli_output.read_text().strip() not in command.stdout + command.stderr
            with psycopg.connect(target.admin) as db:
                assert (
                    db.execute(
                        "SELECT role FROM invitations "
                        "WHERE email_normalized='operator@example.invalid'"
                    ).fetchone()[0]
                    == "staff"
                )
                assert db.execute(
                    "SELECT actor FROM auth_audit_events WHERE action='invitation_issue' "
                    "ORDER BY occurred_at LIMIT 1"
                ).fetchone()[0] == Tokens(config).pseudonym("synthetic-issuer")
            application = create_app(
                Settings(
                    environment="test", auth_enabled=True, database_url=SecretStr(target.runtime)
                )
            )
            with TestClient(application, base_url=ORIGIN) as client:
                assert activation(client, output.read_text().strip()).status_code == 204
                signed_in = login(client, email="operator@example.invalid")
                assert signed_in.status_code == 200
                assert signed_in.json()["user"]["role"] == "staff"
                old_bearer = {"Authorization": "Bearer " + signed_in.json()["access_token"]}
                asyncio.run(
                    run(
                        argparse.Namespace(
                            command="set-role",
                            id=UUID(signed_in.json()["user"]["id"]),
                            role="admin",
                            operator="synthetic-role-operator",
                        )
                    )
                )
                assert client.get("/api/v1/auth/me", headers=old_bearer).status_code == 401
                assert (
                    login(client, email="operator@example.invalid").json()["user"]["role"]
                    == "admin"
                )
                asyncio.run(
                    run(
                        argparse.Namespace(
                            command="disable",
                            id=UUID(signed_in.json()["user"]["id"]),
                            operator="synthetic-role-operator",
                        )
                    )
                )
                assert login(client, email="operator@example.invalid").status_code == 401
            with (
                psycopg.connect(
                    operator_url.replace("postgresql+psycopg:", "postgresql:"), autocommit=True
                ) as db,
                pytest.raises(psycopg.errors.InsufficientPrivilege),
            ):
                db.execute("DELETE FROM auth_audit_events")
            maintenance_url = (
                make_url(target.runtime)
                .set(username=maint_role, password=password)
                .render_as_string(hide_password=False)
            )
            with (
                psycopg.connect(
                    maintenance_url.replace("postgresql+psycopg:", "postgresql:"), autocommit=True
                ) as db,
                pytest.raises(psycopg.errors.InsufficientPrivilege),
            ):
                db.execute("UPDATE users SET role='admin'")
        finally:
            # Revoke/drop only roles created by this fixture; no developer roles.
            with psycopg.connect(target.admin, autocommit=True) as db:
                for role in [op_role, maint_role]:
                    db.execute(sql.SQL("DROP OWNED BY {}").format(sql.Identifier(role)))
            for role in [op_role, maint_role]:
                control.execute(sql.SQL("DROP ROLE IF EXISTS {}").format(sql.Identifier(role)))
