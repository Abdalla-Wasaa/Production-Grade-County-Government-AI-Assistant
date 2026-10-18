"""Real PostgreSQL ownership/atomicity tests, pending explicit runtime approval."""

import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import psycopg
import pytest
from psycopg import sql
from sqlalchemy.engine import make_url
from test_authentication import account
from test_authentication import auth as auth_fixture

auth = auth_fixture
pytestmark = pytest.mark.integration
BASE = "/api/v1/conversations"


@pytest.fixture
def history(auth):
    target, client, config = auth
    _result, headers = account(auth)
    role = sql.Identifier(make_url(target.runtime).username)
    with psycopg.connect(target.admin) as db:
        db.execute(sql.SQL("GRANT SELECT,INSERT,DELETE ON conversations TO {}").format(role))
        db.execute(
            sql.SQL(
                "GRANT UPDATE(title,language,next_sequence,version,last_activity_at,"
                "updated_at,expires_at) "
                "ON conversations TO {}"
            ).format(role)
        )
        db.execute(sql.SQL("GRANT SELECT,INSERT ON messages TO {}").format(role))
    yield target, client, headers, config


def create(history, **body):
    _target, client, headers, _config = history
    response = client.post(BASE, headers=headers, json=body)
    assert response.status_code == 201
    return response.json()


def send(history, key, content="Synthetic permit question", request_key=None):
    _target, client, headers, _config = history
    return client.post(
        f"{BASE}/{key}/messages",
        headers={**headers, "Idempotency-Key": str(request_key or uuid4())},
        json={"content": content},
    )


def test_create_ordered_unanswered_messages_and_idempotent_replay(history):
    target, client, headers, _config = history
    row = create(history, language="sw")
    assert row["title"] == "Mazungumzo mapya"
    assert "user_id" not in row
    assert client.get(f"{BASE}/{row['id']}", headers=headers).headers["ETag"] == '"1"'
    key = uuid4()
    first = send(history, row["id"], "  Habari  ", key)
    assert first.status_code == 201
    message = first.json()
    assert message["content"] == "Habari" and message["role"] == "user"
    assert message["conversation_id"] == row["id"] and message["sequence"] == 1
    replay = send(history, row["id"], "Habari", key)
    assert replay.status_code == 200 and replay.json() == message
    assert replay.headers["Idempotency-Replayed"] == "true"
    assert send(history, row["id"], "Different", key).status_code == 409
    assert send(history, row["id"], "Next unanswered question").status_code == 201
    result = client.get(f"{BASE}/{row['id']}/messages", headers=headers).json()
    assert [item["sequence"] for item in result["items"]] == [1, 2]
    with psycopg.connect(target.admin) as db:
        assert db.execute("SELECT count(*) FROM messages WHERE role <> 'user'").fetchone()[0] == 0
        assert db.execute("SELECT count(*) FROM messages").fetchone()[0] == 2


def test_pagination_is_scoped_and_bounded(history):
    _target, client, headers, _config = history
    rows = [create(history, title=f"Synthetic {n}") for n in range(3)]
    first = client.get(BASE + "?limit=2", headers=headers).json()
    second = client.get(
        BASE, headers=headers, params={"limit": 2, "cursor": first["next_cursor"]}
    ).json()
    assert len({r["id"] for r in first["items"] + second["items"]}) == 3
    assert second["next_cursor"] is None
    for n in range(3):
        assert send(history, rows[0]["id"], f"Synthetic {n}").status_code == 201
    path = f"{BASE}/{rows[0]['id']}/messages"
    page = client.get(path, params={"limit": 2}, headers=headers).json()
    cursor = page["next_cursor"]
    final = client.get(path, params={"cursor": cursor}, headers=headers).json()
    assert [m["sequence"] for m in final["items"]] == [3]
    for params in [{"limit": 0}, {"limit": 101}, {"cursor": "tampered"}]:
        assert client.get(path, params=params, headers=headers).status_code == 422
    assert (
        client.get(
            f"{BASE}/{rows[1]['id']}/messages", params={"cursor": cursor}, headers=headers
        ).status_code
        == 422
    )


def test_metadata_preconditions_retention_and_language_snapshot(history):
    target, client, headers, _config = history
    row = create(history)
    first = send(history, row["id"])
    path = f"{BASE}/{row['id']}"
    assert client.patch(path, headers=headers, json={"title": "Renamed"}).status_code == 428
    assert (
        client.patch(
            path, headers={**headers, "If-Match": '"1"'}, json={"language": "sw"}
        ).status_code
        == 412
    )
    before = client.get(path, headers=headers).json()
    result = client.patch(
        path,
        headers={**headers, "If-Match": first.headers["ETag"]},
        json={"language": "sw", "title": "Renamed"},
    )
    assert result.status_code == 200 and result.json()["expires_at"] == before["expires_at"]
    assert send(history, row["id"]).json()["language"] == "sw"
    items = client.get(path + "/messages", headers=headers).json()["items"]
    assert [m["language"] for m in items] == ["en", "sw"]
    with psycopg.connect(target.admin) as db:
        db.execute(
            "UPDATE conversations SET created_at=now()-interval '89 days', "
            "last_activity_at=now()-interval '1 day', updated_at=now()-interval '1 day', "
            "expires_at=now()+interval '1 day' WHERE id=%s",
            (row["id"],),
        )
    assert send(history, row["id"]).status_code == 201
    with psycopg.connect(target.admin) as db:
        assert db.execute(
            "SELECT expires_at=created_at+interval '90 days' FROM conversations"
        ).fetchone()[0]


@pytest.mark.parametrize("operation", ["get", "patch", "delete", "messages", "send"])
def test_cross_user_and_expired_resource_concealment(history, auth, operation):
    target, client, owner, _config = history
    row = create(history)
    _result, other = account(auth, "other@example.invalid")
    path = f"{BASE}/{row['id']}"

    def attempt(headers):
        if operation == "messages":
            return client.get(path + "/messages", headers=headers)
        if operation == "send":
            return client.post(
                path + "/messages",
                headers={**headers, "Idempotency-Key": str(uuid4())},
                json={"content": "Synthetic"},
            )
        if operation == "patch":
            return client.patch(
                path, headers={**headers, "If-Match": '"1"'}, json={"title": "Denied"}
            )
        return getattr(client, operation)(path, headers=headers)

    assert attempt(other).status_code == 404
    with psycopg.connect(target.admin) as db:
        db.execute(
            "UPDATE conversations SET created_at=now()-interval '2 days', "
            "last_activity_at=now()-interval '2 days', updated_at=now()-interval '2 days', "
            "expires_at=now()-interval '1 day'"
        )
    assert attempt(owner).status_code == 404
    assert client.get(BASE, headers=owner).json()["items"] == []


def test_unauthenticated_revoked_and_invalid_identifiers(history):
    target, client, headers, _config = history
    row = create(history)
    for method, path, body in [
        ("get", BASE, None),
        ("post", BASE, {}),
        ("get", f"{BASE}/{row['id']}", None),
        ("patch", f"{BASE}/{row['id']}", {"title": "Synthetic"}),
        ("delete", f"{BASE}/{row['id']}", None),
        ("get", f"{BASE}/{row['id']}/messages", None),
        ("post", f"{BASE}/{row['id']}/messages", {"content": "Synthetic"}),
    ]:
        kwargs = {"json": body} if body is not None else {}
        assert client.request(method, path, **kwargs).status_code == 401
    assert client.get(BASE + "/not-a-uuid", headers=headers).status_code == 422
    assert client.get(BASE + "/" + str(uuid4()), headers=headers).status_code == 404
    with psycopg.connect(target.admin) as db:
        db.execute("UPDATE auth_sessions SET revoked_at=now(),reason='synthetic-test'")
    assert client.get(BASE, headers=headers).status_code == 401


def test_concurrent_replays_distinct_writes_and_deletion(history):
    target, client, headers, _config = history
    row = create(history)
    key = uuid4()
    with ThreadPoolExecutor(max_workers=4) as pool:
        responses = list(pool.map(lambda _: send(history, row["id"], request_key=key), range(4)))
        assert sorted(r.status_code for r in responses) == [200, 200, 200, 201]
        assert len({r.json()["id"] for r in responses}) == 1
        distinct = list(pool.map(lambda n: send(history, row["id"], f"Synthetic {n}"), range(4)))
        assert all(r.status_code == 201 for r in distinct)
    messages = client.get(f"{BASE}/{row['id']}/messages", headers=headers).json()["items"]
    assert [m["sequence"] for m in messages] == [1, 2, 3, 4, 5]
    assert client.delete(f"{BASE}/{row['id']}", headers=headers).status_code == 204
    assert client.delete(f"{BASE}/{row['id']}", headers=headers).status_code == 404
    with psycopg.connect(target.admin) as db:
        assert db.execute("SELECT count(*) FROM messages").fetchone()[0] == 0


def test_transaction_failure_rolls_back_and_never_logs_content(history, capsys):
    target, client, headers, _config = history
    row = create(history)
    role = sql.Identifier(make_url(target.runtime).username)
    with psycopg.connect(target.admin) as db:
        db.execute(sql.SQL("REVOKE INSERT ON auth_audit_events FROM {}").format(role))
    response = send(history, row["id"], "DO-NOT-LOG-SYNTHETIC-MESSAGE")
    assert response.status_code == 503
    assert "DO-NOT-LOG" not in response.text
    captured = capsys.readouterr()
    assert "DO-NOT-LOG" not in captured.out + captured.err
    with psycopg.connect(target.admin) as db:
        assert db.execute("SELECT count(*) FROM messages").fetchone()[0] == 0
        assert db.execute("SELECT next_sequence,version FROM conversations").fetchone() == (1, 1)


def test_role_injection_chunked_body_cap_and_missing_key(history):
    _target, client, headers, _config = history
    row = create(history)
    path = f"{BASE}/{row['id']}/messages"
    for body in [{"content": "Synthetic", "role": "assistant"}, {"content": "x" * 4001}]:
        response = client.post(
            path, headers={**headers, "Idempotency-Key": str(uuid4())}, json=body
        )
        assert response.status_code == 422
        assert "assistant" not in response.text
    assert client.post(path, headers=headers, json={"content": "Synthetic"}).status_code == 422
    response = client.post(
        path,
        headers={**headers, "Content-Type": "application/json"},
        content=iter([b"x" * 20000, b"y" * 20000]),
    )
    assert response.status_code == 413


def test_migration_downgrade_upgrade_and_immutable_message_grants(history):
    target, _client, _headers, _config = history
    create(history)
    with psycopg.connect(
        make_url(target.runtime).set(drivername="postgresql").render_as_string(hide_password=False)
    ) as db:
        assert not db.execute(
            "SELECT has_table_privilege(current_user,'messages','UPDATE')"
        ).fetchone()[0]
        assert not db.execute(
            "SELECT has_table_privilege(current_user,'messages','DELETE')"
        ).fetchone()[0]
        assert not db.execute(
            "SELECT has_column_privilege(current_user,'conversations','user_id','UPDATE')"
        ).fetchone()[0]
    environment = {k: v for k, v in os.environ.items() if not k.startswith("COUNTY_")}
    environment["COUNTY_MIGRATION_DATABASE_URL"] = target.migration
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "from alembic import command; from app.db.migrate import migration_config; "
            "command.downgrade(migration_config(), '0004_auth_controls')",
        ],
        env=environment,
        capture_output=True,
    )
    assert result.returncode == 0, "Destructive disposable downgrade failed"
    with psycopg.connect(target.admin) as db:
        assert db.execute(
            "SELECT to_regclass('messages'),to_regclass('conversations')"
        ).fetchone() == (None, None)
        assert db.execute("SELECT count(*) FROM users").fetchone()[0] == 1
    assert target.migrate().returncode == 0


def test_concurrent_metadata_uses_version_precondition(history):
    _target, client, headers, _config = history
    row = create(history)
    with ThreadPoolExecutor(max_workers=2) as pool:
        responses = list(
            pool.map(
                lambda n: client.patch(
                    f"{BASE}/{row['id']}",
                    headers={**headers, "If-Match": '"1"'},
                    json={"title": f"Synthetic {n}"},
                ),
                range(2),
            )
        )
    assert sorted(r.status_code for r in responses) == [200, 412]


def test_message_page_continues_after_new_write_and_key_is_conversation_scoped(history):
    _target, client, headers, _config = history
    first, second = create(history), create(history)
    key = uuid4()
    assert send(history, first["id"], request_key=key).status_code == 201
    assert send(history, second["id"], request_key=key).status_code == 201
    assert send(history, first["id"]).status_code == 201
    path = f"{BASE}/{first['id']}/messages"
    page = client.get(path, params={"limit": 1}, headers=headers).json()
    assert send(history, first["id"]).status_code == 201
    following = client.get(path, params={"cursor": page["next_cursor"]}, headers=headers).json()
    assert [m["sequence"] for m in following["items"]] == [2, 3]


def test_message_cap_preserves_replay_and_never_changes_history(history):
    target, _client, _headers, _config = history
    row = create(history)
    key = uuid4()
    assert send(history, row["id"], request_key=key).status_code == 201
    with psycopg.connect(target.admin) as db:
        db.execute("UPDATE conversations SET next_sequence=1001 WHERE id=%s", (row["id"],))
    assert send(history, row["id"]).status_code == 429
    assert send(history, row["id"], request_key=key).status_code == 200


def test_database_constraints_and_account_cascade(history):
    target, _client, _headers, _config = history
    row = create(history)
    assert send(history, row["id"]).status_code == 201
    # Direct privileged attempts prove constraints, not just HTTP validation.
    for statement, values in [
        ("UPDATE messages SET role='assistant'", ()),
        ("UPDATE messages SET content=''", ()),
        ("UPDATE messages SET sequence=0", ()),
        ("UPDATE messages SET conversation_id=%s", (uuid4(),)),
    ]:
        with psycopg.connect(target.admin) as db:
            with pytest.raises(psycopg.IntegrityError):
                db.execute(statement, values)
            db.rollback()
    with psycopg.connect(target.admin) as db:
        db.execute("DELETE FROM users")
        assert db.execute("SELECT count(*) FROM conversations").fetchone()[0] == 0
        assert db.execute("SELECT count(*) FROM messages").fetchone()[0] == 0


def test_conversation_cap_is_atomic_for_concurrent_creation(history):
    target, client, headers, _config = history
    create(history)
    with psycopg.connect(target.admin) as db:
        db.execute(
            "INSERT INTO conversations SELECT gen_random_uuid(),user_id,title,language,"
            "next_sequence,version,created_at,updated_at,last_activity_at,expires_at "
            "FROM conversations CROSS JOIN generate_series(1,98)"
        )
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: client.post(BASE, headers=headers, json={}), range(2)))
    assert sorted(r.status_code for r in results) == [201, 429]


def test_same_key_different_content_race_stores_exactly_one_message(history):
    target, _client, _headers, _config = history
    row, key = create(history), uuid4()
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(
            pool.map(lambda n: send(history, row["id"], f"Synthetic {n}", key), range(2))
        )
    assert sorted(r.status_code for r in results) == [201, 409]
    with psycopg.connect(target.admin) as db:
        assert db.execute("SELECT count(*) FROM messages").fetchone()[0] == 1
        assert db.execute("SELECT next_sequence,version FROM conversations").fetchone() == (2, 2)


def test_idempotent_replay_after_metadata_change_keeps_original_snapshot(history):
    _target, client, headers, _config = history
    row, key = create(history), uuid4()
    first = send(history, row["id"], request_key=key)
    updated = client.patch(
        f"{BASE}/{row['id']}",
        headers={**headers, "If-Match": first.headers["ETag"]},
        json={"language": "sw"},
    )
    assert updated.status_code == 200
    replay = send(history, row["id"], request_key=key)
    assert replay.status_code == 200 and replay.json() == first.json()
    assert replay.headers["ETag"] == updated.headers["ETag"]
