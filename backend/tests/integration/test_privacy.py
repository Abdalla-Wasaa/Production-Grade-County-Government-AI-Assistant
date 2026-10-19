"""Prepared real-role PostgreSQL privacy acceptance; synthetic/disposable opt-in only."""

import asyncio
import base64
import os
import secrets
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from time import perf_counter
from uuid import UUID, uuid4

import psycopg
import pytest
from psycopg import sql
from sqlalchemy.engine import make_url
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool
from test_authentication import account
from test_authentication import auth as auth_fixture
from test_conversations import create, send
from test_conversations import history as history_fixture

from app.modules.identity.grants import grant
from app.modules.identity.security import AuthFailure, Tokens
from app.modules.privacy.schemas import DeleteAccountCommand, HoldCommand
from app.modules.privacy.service import MAINTENANCE_LOCK, Privacy

auth = auth_fixture
history = history_fixture
pytestmark = pytest.mark.integration


@pytest.fixture
def lifecycle(history, monkeypatch):
    target, _client, _headers, config = history
    names = (target.name + "_p", target.name + "_s")
    password = secrets.token_urlsafe(24)
    global_admin = (
        make_url(target.admin).set(database="postgres").render_as_string(hide_password=False)
    )
    created = []
    try:
        with psycopg.connect(global_admin, autocommit=True) as admin:
            for name in names:
                admin.execute(
                    sql.SQL("CREATE ROLE {} LOGIN PASSWORD {}").format(
                        sql.Identifier(name), sql.Literal(password)
                    )
                )
                created.append(name)
        monkeypatch.setenv("COUNTY_MIGRATION_DATABASE_URL", target.migration)
        key = base64.b64decode(config.throttle_secret.get_secret_value())
        asyncio.run(grant(make_url(target.runtime).username, *names, privacy_key=key))
        urls = [
            make_url(target.migration)
            .set(username=n, password=password)
            .render_as_string(hide_password=False)
            for n in names
        ]

        def operate(command, *, maintenance=False, clock=None, audit_key=None):
            async def work():
                engine = create_async_engine(
                    urls[int(maintenance)], poolclass=NullPool, hide_parameters=True
                )
                try:
                    async with (
                        async_sessionmaker(engine, expire_on_commit=False)() as db,
                        db.begin(),
                    ):
                        store = Privacy(db, audit_key or key, **({"clock": clock} if clock else {}))
                        return await command(store)
                finally:
                    await engine.dispose()

            return asyncio.run(work())

        yield history, operate, urls, key
    finally:
        with psycopg.connect(target.admin, autocommit=True) as db:
            for name in created:
                db.execute(sql.SQL("DROP OWNED BY {}").format(sql.Identifier(name)))
                db.execute(
                    sql.SQL("REVOKE ALL ON DATABASE {} FROM {}").format(
                        sql.Identifier(target.name), sql.Identifier(name)
                    )
                )
        with psycopg.connect(global_admin, autocommit=True) as admin:
            for name in created:
                admin.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(name)))


def owner(history):
    target, _client, _headers, _config = history
    with psycopg.connect(target.admin) as db:
        return db.execute("SELECT id FROM users ORDER BY created_at LIMIT 1").fetchone()[0]


def hold(lifecycle, conversation=None):
    history, operate, _urls, _key = lifecycle
    return operate(
        lambda s: s.create_hold(
            HoldCommand(
                id=uuid4(),
                scope="conversation" if conversation else "account",
                target_id=UUID(conversation) if conversation else owner(history),
                reason="incident",
                case_ref=uuid4(),
            )
        )
    )


def request(lifecycle, key=None):
    history, operate, _urls, _key = lifecycle
    command = DeleteAccountCommand(
        id=key or uuid4(), user_id=owner(history), verification_ref=uuid4(), verified=True
    )
    return command, operate(lambda s: s.request_deletion(command))


def expire(history, conversation):
    target, _client, _headers, _config = history
    with psycopg.connect(target.admin) as db:
        db.execute(
            "UPDATE conversations SET created_at=now()-interval '40 days',"
            "last_activity_at=now()-interval '32 days',expires_at=now()-interval '2 days' "
            "WHERE id=%s",
            (conversation,),
        )


def test_hold_changes_are_authorized_idempotent_and_content_free(lifecycle):
    history, operate, _urls, _key = lifecycle
    command = HoldCommand(
        id=uuid4(), scope="account", target_id=owner(history), reason="records", case_ref=uuid4()
    )
    row = operate(lambda s: s.create_hold(command))
    assert operate(lambda s: s.create_hold(command)).id == row.id
    operate(lambda s: s.change_hold(row.id, uuid4(), release=False))
    operate(lambda s: s.change_hold(row.id, uuid4(), release=True))
    assert operate(lambda s: s.change_hold(row.id, uuid4(), release=True)).released_at is not None
    with psycopg.connect(history[0].admin) as db:
        rows = db.execute(
            "SELECT action,actor,subject FROM auth_audit_events WHERE request_id=%s "
            "ORDER BY occurred_at",
            (row.id,),
        ).fetchall()
        assert [r[0] for r in rows] == [
            "privacy_hold_created",
            "privacy_hold_reviewed",
            "privacy_hold_released",
        ]
        assert all(len(r[1]) == 64 and len(r[2]) == 64 for r in rows)


def test_runtime_and_maintenance_cannot_issue_holds(lifecycle):
    history, operate, urls, key = lifecycle
    command = HoldCommand(
        id=uuid4(), scope="account", target_id=owner(history), reason="review", case_ref=uuid4()
    )
    with pytest.raises(AuthFailure) as error:
        operate(lambda s: s.create_hold(command), maintenance=True)
    assert error.value.status == 403

    async def runtime():
        engine = create_async_engine(history[0].runtime, poolclass=NullPool, hide_parameters=True)
        try:
            async with async_sessionmaker(engine)() as db, db.begin():
                await Privacy(db, key).create_hold(command)
        finally:
            await engine.dispose()

    with pytest.raises(AuthFailure) as error:
        asyncio.run(runtime())
    assert error.value.status == 403


def test_revoked_operator_fails_closed(lifecycle):
    history, operate, urls, _key = lifecycle
    with psycopg.connect(history[0].admin) as db:
        db.execute(
            "UPDATE privacy_operators SET enabled=false WHERE role_name=%s",
            (make_url(urls[0]).username,),
        )
    with pytest.raises(AuthFailure) as error:
        hold(lifecycle)
    assert error.value.status == 403


def test_hold_conflicting_retry_is_not_silently_reused(lifecycle):
    history, operate, _urls, _key = lifecycle
    row = hold(lifecycle)
    with pytest.raises(AuthFailure) as error:
        operate(
            lambda s: s.create_hold(
                HoldCommand(
                    id=row.id,
                    scope="account",
                    target_id=owner(history),
                    reason="review",
                    case_ref=uuid4(),
                )
            )
        )
    assert error.value.status == 409


def test_held_conversation_delete_returns_safe_409_and_other_user_404(lifecycle):
    history, _operate, _urls, _key = lifecycle
    target, client, headers, config = history
    row = create(history)
    hold(lifecycle, row["id"])
    response = client.delete("/api/v1/conversations/" + row["id"], headers=headers)
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "deletion_restricted"
    assert "incident" not in response.text
    _, other = account((target, client, config), email="other-privacy@example.invalid")
    assert client.delete("/api/v1/conversations/" + row["id"], headers=other).status_code == 404


def test_database_delete_guard_blocks_cascade_bypass(lifecycle):
    history, _operate, _urls, _key = lifecycle
    row = create(history)
    assert send(history, row["id"]).status_code == 201
    hold(lifecycle, row["id"])
    with psycopg.connect(history[0].admin) as db:
        with pytest.raises(psycopg.errors.CheckViolation):
            db.execute("DELETE FROM users WHERE id=%s", (owner(history),))
        db.rollback()
        assert db.execute("SELECT count(*) FROM messages").fetchone()[0] == 1


def test_expired_held_history_is_hidden_but_not_physically_purged(lifecycle):
    history, operate, _urls, _key = lifecycle
    row = create(history)
    hold(lifecycle, row["id"])
    expire(history, row["id"])
    assert (
        history[1].get("/api/v1/conversations/" + row["id"], headers=history[2]).status_code == 404
    )
    result = operate(lambda s: s.maintenance(force=True), maintenance=True)
    assert result.conversations == 0
    with psycopg.connect(history[0].admin) as db:
        assert db.execute("SELECT count(*) FROM conversations").fetchone()[0] == 1


def test_request_acceptance_immediately_disables_and_revokes(lifecycle):
    history, operate, _urls, _key = lifecycle
    command, row = request(lifecycle)
    assert row.status == "accepted"
    assert operate(lambda s: s.request_deletion(command)).id == row.id
    assert history[1].get("/api/v1/auth/me", headers=history[2]).status_code == 401
    with psycopg.connect(history[0].admin) as db:
        assert db.execute("SELECT status FROM users").fetchone()[0] == "disabled"
        assert (
            db.execute("SELECT count(*) FROM auth_sessions WHERE revoked_at IS NULL").fetchone()[0]
            == 0
        )


def test_account_completion_cascades_and_retry_after_deletion_is_safe(lifecycle):
    history, operate, _urls, _key = lifecycle
    row = create(history)
    assert send(history, row["id"]).status_code == 201
    command, accepted = request(lifecycle)
    result = operate(lambda s: s.maintenance(force=True), maintenance=True)
    assert result.accounts == 1
    assert operate(lambda s: s.request_deletion(command)).status == "completed"
    assert operate(lambda s: s.request_status(accepted.id)).user_id is None
    with psycopg.connect(history[0].admin) as db:
        for table in (
            "users",
            "conversations",
            "messages",
            "auth_sessions",
            "refresh_tokens",
            "invitations",
        ):
            assert (
                db.execute(
                    sql.SQL("SELECT count(*) FROM {}").format(sql.Identifier(table))
                ).fetchone()[0]
                == 0
            )
        assert db.execute("SELECT count(*) FROM privacy_deletion_ledger").fetchone()[0] == 2


def test_held_request_preserves_only_held_conversations_then_completes(lifecycle):
    history, operate, _urls, _key = lifecycle
    kept = create(history)
    create(history)
    active = hold(lifecycle, kept["id"])
    command, accepted = request(lifecycle)
    assert accepted.status == "held"
    operate(lambda s: s.maintenance(force=True), maintenance=True)
    with psycopg.connect(history[0].admin) as db:
        assert db.execute("SELECT id FROM conversations").fetchall() == [(UUID(kept["id"]),)]
        assert db.execute("SELECT status FROM users").fetchone()[0] == "disabled"
    operate(lambda s: s.change_hold(active.id, uuid4(), release=True))
    operate(lambda s: s.maintenance(force=True), maintenance=True)
    assert operate(lambda s: s.request_status(command.id)).status == "completed"


def test_missed_daily_run_catches_up_and_repeat_is_idle(lifecycle):
    history, operate, _urls, _key = lifecycle
    row = create(history)
    expire(history, row["id"])
    result = operate(lambda s: s.maintenance(), maintenance=True)
    assert result.conversations == 1 and not result.backlog
    assert operate(lambda s: s.maintenance(), maintenance=True).status == "idle"


def test_batch_backlog_does_not_silently_stamp_daily_completion(lifecycle):
    history, operate, _urls, _key = lifecycle
    for _ in range(3):
        row = create(history)
        expire(history, row["id"])
    first = operate(lambda s: s.maintenance(limit=1), maintenance=True)
    assert first.conversations == 1 and first.backlog and first.status == "attention"
    with psycopg.connect(history[0].admin) as db:
        assert (
            db.execute("SELECT last_daily_at FROM privacy_maintenance_state").fetchone()[0] is None
        )
    for _ in range(2):
        operate(lambda s: s.maintenance(limit=1), maintenance=True)
    assert operate(lambda s: s.maintenance(), maintenance=True).status == "idle"


def test_concurrent_maintenance_is_idempotent_and_nonblocking(lifecycle):
    history, operate, _urls, _key = lifecycle
    row = create(history)
    expire(history, row["id"])
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(
            pool.map(
                lambda _: operate(lambda s: s.maintenance(force=True), maintenance=True), range(2)
            )
        )
    assert sum(r.conversations for r in results) == 1
    with psycopg.connect(history[0].admin) as db:
        assert db.execute("SELECT count(*) FROM privacy_deletion_ledger").fetchone()[0] == 1


def test_existing_maintenance_lock_returns_busy(lifecycle):
    history, operate, _urls, _key = lifecycle
    with psycopg.connect(history[0].admin) as db:
        db.execute("SELECT pg_advisory_xact_lock(%s)", (MAINTENANCE_LOCK,))
        assert operate(lambda s: s.maintenance(force=True), maintenance=True).status == "busy"


def test_overdue_hold_alerts_and_never_automatically_releases(lifecycle):
    history, operate, _urls, _key = lifecycle
    row = hold(lifecycle)
    future = row.review_due_at + timedelta(seconds=1)
    report = operate(lambda s: s.maintenance(), maintenance=True, clock=lambda: future)
    assert report.overdue_holds == 1 and report.status == "attention"
    with psycopg.connect(history[0].admin) as db:
        assert db.execute("SELECT released_at FROM privacy_holds").fetchone()[0] is None
    reviewed = operate(
        lambda s: s.change_hold(row.id, uuid4(), release=False), clock=lambda: future
    )
    assert reviewed.review_due_at == future + timedelta(days=30)
    assert (
        operate(lambda s: s.maintenance(), maintenance=True, clock=lambda: future).overdue_holds
        == 0
    )


def test_hold_preserves_correlated_old_audits_until_release(lifecycle):
    history, operate, _urls, _key = lifecycle
    row = hold(lifecycle)
    event = uuid4()
    with psycopg.connect(history[0].admin) as db:
        db.execute(
            "INSERT INTO auth_audit_events VALUES(%s,now()-interval '91 days',NULL,%s,"
            "'synthetic_event','success',%s)",
            (event, Tokens(history[3]).pseudonym(str(owner(history))), uuid4()),
        )
    operate(lambda s: s.maintenance(force=True), maintenance=True)
    with psycopg.connect(history[0].admin) as db:
        assert (
            db.execute("SELECT count(*) FROM auth_audit_events WHERE id=%s", (event,)).fetchone()[0]
            == 1
        )
    operate(lambda s: s.change_hold(row.id, uuid4(), release=True))
    operate(lambda s: s.maintenance(force=True), maintenance=True)
    with psycopg.connect(history[0].admin) as db:
        assert (
            db.execute("SELECT count(*) FROM auth_audit_events WHERE id=%s", (event,)).fetchone()[0]
            == 0
        )


@pytest.mark.parametrize("action", ["privacy_hold_created", "privacy_delete_accepted"])
def test_mandatory_audit_failure_rolls_back_control_and_revocation(lifecycle, action):
    history, operate, _urls, _key = lifecycle
    with psycopg.connect(history[0].admin) as db:
        # action is from a fixed test enum, never user input.
        db.execute(
            sql.SQL(
                "CREATE FUNCTION privacy_test_fail() RETURNS trigger LANGUAGE plpgsql AS "
                "$$ BEGIN IF NEW.action={} THEN RAISE EXCEPTION 'synthetic audit failure'; END IF; "
                "RETURN NEW; END $$"
            ).format(sql.Literal(action))
        )
        db.execute(
            "CREATE TRIGGER privacy_test_fail BEFORE INSERT ON auth_audit_events "
            "FOR EACH ROW EXECUTE FUNCTION privacy_test_fail()"
        )
    with pytest.raises(DBAPIError):
        hold(lifecycle) if action == "privacy_hold_created" else request(lifecycle)
    with psycopg.connect(history[0].admin) as db:
        assert db.execute("SELECT status FROM users").fetchone()[0] == "active"
        assert db.execute("SELECT count(*) FROM privacy_deletion_requests").fetchone()[0] == 0
        assert db.execute("SELECT count(*) FROM privacy_holds").fetchone()[0] == 0


def test_wrong_pseudonym_key_fails_closed_without_mutation(lifecycle):
    with pytest.raises(AuthFailure) as error:
        lifecycle[1](lambda s: s.authorize("can_hold"), audit_key=bytes(range(32)))
    assert error.value.status == 503


def test_privacy_revision_pristine_downgrade_and_upgrade(target):
    assert target.migrate().returncode == 0
    env = {k: v for k, v in os.environ.items() if not k.startswith("COUNTY_")}
    env["COUNTY_MIGRATION_DATABASE_URL"] = target.migration
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "from alembic import command;"
            "from app.db.migrate import migration_config,MigrationSettings;"
            "c=migration_config();"
            "c.attributes['database_url']=MigrationSettings().migration_database_url;"
            "command.downgrade(c,'0005_conversation_persistence')",
        ],
        env=env,
        capture_output=True,
    )
    assert result.returncode == 0
    assert target.migrate().returncode == 0


def test_retained_hold_evidence_blocks_downgrade(lifecycle):
    hold(lifecycle)
    target = lifecycle[0][0]
    env = {k: v for k, v in os.environ.items() if not k.startswith("COUNTY_")}
    env["COUNTY_MIGRATION_DATABASE_URL"] = target.migration
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "from alembic import command;"
            "from app.db.migrate import migration_config,MigrationSettings;"
            "c=migration_config();"
            "c.attributes['database_url']=MigrationSettings().migration_database_url;"
            "command.downgrade(c,'0005_conversation_persistence')",
        ],
        env=env,
        capture_output=True,
    )
    assert result.returncode != 0
    assert target.migrate("check").returncode == 0


def test_twenty_three_hour_catchup_does_not_wait_for_next_daily_run(lifecycle):
    history, operate, _urls, _key = lifecycle
    row = create(history)
    expire(history, row["id"])
    now = datetime.now(UTC)
    with psycopg.connect(history[0].admin) as db:
        db.execute("UPDATE privacy_maintenance_state SET last_daily_at=%s", (now,))
        db.execute(
            "UPDATE conversations SET expires_at=%s WHERE id=%s",
            (now - timedelta(hours=23, minutes=1), row["id"]),
        )
    result = operate(lambda s: s.maintenance(), maintenance=True, clock=lambda: now)
    assert result.conversations == 1
    assert not result.deadline_breached


def test_exact_retention_boundary_is_invisible_and_cannot_be_resurrected(lifecycle, monkeypatch):
    history, operate, _urls, _key = lifecycle
    row = create(history)
    boundary = datetime.now(UTC) + timedelta(seconds=2)
    with psycopg.connect(history[0].admin) as db:
        db.execute("UPDATE conversations SET expires_at=%s WHERE id=%s", (boundary, row["id"]))
    monkeypatch.setattr(
        history[1].app.state.auth_tokens, "clock", lambda: boundary - timedelta(microseconds=1)
    )
    assert (
        history[1].get("/api/v1/conversations/" + row["id"], headers=history[2]).status_code == 200
    )
    monkeypatch.setattr(history[1].app.state.auth_tokens, "clock", lambda: boundary)
    assert (
        history[1].get("/api/v1/conversations/" + row["id"], headers=history[2]).status_code == 404
    )
    assert (
        history[1]
        .patch(
            "/api/v1/conversations/" + row["id"],
            headers=history[2],
            json={"title": "Synthetic retry"},
        )
        .status_code
        == 404
    )
    assert (
        operate(
            lambda s: s.maintenance(force=True), maintenance=True, clock=lambda: boundary
        ).conversations
        == 1
    )


def test_identity_batch_backlog_is_reported_and_catches_up(lifecycle):
    history, operate, _urls, _key = lifecycle
    now = datetime.now(UTC)
    with psycopg.connect(history[0].admin) as db:
        for _ in range(3):
            db.execute(
                "INSERT INTO auth_sessions VALUES(%s,%s,now()-interval '9 days',"
                "now()-interval '2 days',now()-interval '9 days',NULL,NULL)",
                (uuid4(), owner(history)),
            )
    result = operate(lambda s: s.maintenance(limit=1), maintenance=True, clock=lambda: now)
    assert result.backlog and result.status == "attention"
    for _ in range(2):
        operate(lambda s: s.maintenance(limit=1), maintenance=True, clock=lambda: now)
    with psycopg.connect(history[0].admin) as db:
        assert (
            db.execute(
                "SELECT count(*) FROM auth_sessions WHERE expires_at<=%s", (now,)
            ).fetchone()[0]
            == 0
        )


def test_conflicting_deletion_key_never_disables_another_account(lifecycle):
    command, _row = request(lifecycle)
    with pytest.raises(AuthFailure) as error:
        lifecycle[1](lambda s: s.request_deletion(command.model_copy(update={"user_id": uuid4()})))
    assert error.value.code == "idempotency_conflict"


def test_physical_deletion_and_ledger_roll_back_when_audit_fails(lifecycle):
    history, operate, _urls, _key = lifecycle
    row = create(history)
    assert send(history, row["id"]).status_code == 201
    command, _accepted = request(lifecycle)
    with psycopg.connect(history[0].admin) as db:
        db.execute(
            "CREATE FUNCTION privacy_test_fail() RETURNS trigger LANGUAGE plpgsql AS $$ "
            "BEGIN IF NEW.action='privacy_account_deleted' THEN "
            "RAISE EXCEPTION 'synthetic audit failure'; END IF; RETURN NEW; END $$"
        )
        db.execute(
            "CREATE TRIGGER privacy_test_fail BEFORE INSERT ON auth_audit_events "
            "FOR EACH ROW EXECUTE FUNCTION privacy_test_fail()"
        )
    with pytest.raises(DBAPIError):
        operate(lambda s: s.maintenance(force=True), maintenance=True)
    with psycopg.connect(history[0].admin) as db:
        assert db.execute("SELECT status FROM users").fetchone()[0] == "disabled"
        assert db.execute("SELECT count(*) FROM messages").fetchone()[0] == 1
        assert db.execute("SELECT count(*) FROM privacy_deletion_ledger").fetchone()[0] == 0
    assert operate(lambda s: s.request_status(command.id)).status == "accepted"


def test_fully_held_request_does_not_starve_later_eligible_account(lifecycle):
    history, operate, _urls, _key = lifecycle
    hold(lifecycle)
    first, _accepted = request(lifecycle)
    target, client, _headers, config = history
    result, _bearer = account((target, client, config), email="eligible@example.invalid")
    second = DeleteAccountCommand(
        id=uuid4(), user_id=UUID(result["user"]["id"]), verification_ref=uuid4(), verified=True
    )
    operate(lambda s: s.request_deletion(second))
    report = operate(lambda s: s.maintenance(limit=1, force=True), maintenance=True)
    assert report.accounts == 1
    assert operate(lambda s: s.request_status(first.id)).status == "held"
    assert operate(lambda s: s.request_status(second.id)).status == "completed"


def test_documented_parent_batch_capacity_with_synthetic_cascades(lifecycle, record_property):
    history, operate, _urls, _key = lifecycle
    row = create(history)
    now = datetime.now(UTC)
    with psycopg.connect(history[0].admin) as db:
        db.execute(
            "UPDATE conversations SET created_at=%s,last_activity_at=%s,"
            "updated_at=%s,expires_at=%s WHERE id=%s",
            (
                now - timedelta(days=40),
                now - timedelta(days=31),
                now - timedelta(days=31),
                now - timedelta(hours=23, minutes=30),
                row["id"],
            ),
        )
        db.execute(
            "INSERT INTO conversations SELECT gen_random_uuid(),user_id,title,language,"
            "6,1,created_at,updated_at,last_activity_at,expires_at "
            "FROM conversations CROSS JOIN generate_series(1,99) WHERE id=%s",
            (row["id"],),
        )
        db.execute(
            "INSERT INTO messages SELECT gen_random_uuid(),c.id,n,'user',"
            "'Synthetic capacity fixture','en',gen_random_uuid(),repeat('0',64),c.last_activity_at "
            "FROM conversations c CROSS JOIN generate_series(1,5) n"
        )
        # Exercise the urgent catch-up path rather than claiming the daily timer ran.
        db.execute("UPDATE privacy_maintenance_state SET last_daily_at=%s", (now,))
    started = perf_counter()
    result = operate(lambda s: s.maintenance(limit=100), maintenance=True, clock=lambda: now)
    elapsed = perf_counter() - started
    record_property("synthetic_purge_seconds", elapsed)
    assert result.conversations == 100 and not result.backlog
    assert not result.deadline_breached and elapsed < 300
    with psycopg.connect(history[0].admin) as db:
        assert db.execute("SELECT count(*) FROM messages").fetchone()[0] == 0
        assert db.execute("SELECT count(*) FROM conversations").fetchone()[0] == 0
        assert db.execute("SELECT count(*) FROM privacy_deletion_ledger").fetchone()[0] == 100
