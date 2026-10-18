"""Negative cryptographic/configuration contracts; no database or network."""

import hashlib
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from uuid import uuid4

import jwt
import pytest
from auth_helpers import auth_settings
from fastapi.testclient import TestClient
from pydantic import SecretStr, ValidationError

from app.core.config import ConfigurationError, Settings
from app.main import create_app
from app.modules.identity.http import origin, require_role
from app.modules.identity.operator import token_file
from app.modules.identity.schemas import Activation, Login
from app.modules.identity.security import AuthFailure, Passwords, Tokens, digest, random_token


def test_tokens_are_random_canonical_and_only_digests_are_stored():
    first, second = random_token(), random_token()
    assert first != second and len(first) == 43
    assert digest(first) == hashlib.sha256(first.encode()).hexdigest()
    for value in ["", "short", first + "=", "!" * 43, "_" * 43]:
        with pytest.raises(AuthFailure):
            digest(value)


def test_access_claim_validation_and_expiration(tmp_path):
    config = auth_settings(tmp_path)
    now = datetime(2026, 10, 17, tzinfo=UTC)
    tokens = Tokens(config, lambda: now)
    user, family = uuid4(), uuid4()
    encoded = tokens.access(user, family, 2)
    claims = tokens.decode_access(encoded)
    assert claims["sub"] == str(user) and claims["token_version"] == 2
    for field, value in [
        ("iss", "other"),
        ("aud", "other"),
        ("sub", "bad"),
        ("sid", "bad"),
        ("token_version", True),
        ("token_version", -1),
        ("exp", int(now.timestamp()) - 1),
        ("iat", int(now.timestamp()) + 60),
    ]:
        forged = {**claims, field: value}
        with pytest.raises(AuthFailure):
            tokens.decode_access(jwt.encode(forged, tokens.signing, algorithm="HS256"))
    with pytest.raises(AuthFailure):
        tokens.decode_access(jwt.encode(claims, None, algorithm="none"))
    with pytest.raises(AuthFailure):
        Tokens(config, lambda: now + timedelta(minutes=16)).decode_access(encoded)


def test_csrf_context_binding_purpose_and_expiry(tmp_path):
    config = auth_settings(tmp_path)
    now = datetime(2026, 10, 17, tzinfo=UTC)
    tokens = Tokens(config, lambda: now)
    signed = tokens.sign_context("csrf", "anonymous", 1800)
    assert tokens.context(signed, "csrf", "anonymous")
    for purpose, subject in [("sessions_cursor", "anonymous"), ("csrf", str(uuid4()))]:
        with pytest.raises(AuthFailure):
            tokens.context(signed, purpose, subject)
    with pytest.raises(AuthFailure):
        Tokens(config, lambda: now + timedelta(minutes=31)).context(signed, "csrf", "anonymous")


async def test_argon_hash_policy_verification_and_bounded_work(tmp_path):
    config = auth_settings(tmp_path)
    passwords = Passwords(config)
    encoded = await passwords.hash("a synthetic unique passphrase 27")
    assert encoded.startswith("$argon2id$") and "m=65536,t=3,p=1" in encoded
    assert await passwords.verify("a synthetic unique passphrase 27", encoded)
    assert not await passwords.verify("incorrect synthetic passphrase", encoded)
    assert not await passwords.verify("unknown account", None)
    with pytest.raises(AuthFailure):
        await passwords.hash("commonly-guessed-synthetic-password")
    other_request = object()
    passwords.capacity.acquire_on_behalf_of_nowait(other_request)
    try:
        with pytest.raises(AuthFailure) as failure:
            await passwords.hash("another synthetic passphrase 28")
        assert failure.value.status == 503
    finally:
        passwords.capacity.release_on_behalf_of(other_request)
    config.password_blocklist.write_text("changed")
    with pytest.raises(ValueError):
        Passwords(config)


def test_strict_inputs_roles_and_unicode():
    body = Login(email=" Pilot@Example.Invalid ", password=SecretStr("sample"))
    assert body.email == "pilot@example.invalid"
    with pytest.raises(ValidationError):
        Login(email="pilot@example.invalid", password=SecretStr("sample"), role="admin")
    for bad in ["short", "x" * 129, "validlength\x00password"]:
        with pytest.raises(ValidationError):
            Activation(
                token=SecretStr(random_token()),
                password=SecretStr(bad),
                preferred_language="en",
                privacy_notice_version="v1",
                privacy_notice_acknowledged=True,
            )
    for role in ["citizen", "staff", "admin"]:
        require_role(SimpleNamespace(role=role), role)
        with pytest.raises(AuthFailure) as failure:
            require_role(SimpleNamespace(role=role), "unapproved-capability")
        assert failure.value.status == 403


def test_origin_does_not_trust_host_or_forwarded_headers(tmp_path):
    tokens = Tokens(auth_settings(tmp_path))
    for headers in [
        {},
        {"origin": "null"},
        {"origin": "http://attacker.invalid"},
        {"origin": "http://attacker.invalid", "referer": "http://127.0.0.1/login"},
    ]:
        with pytest.raises(AuthFailure):
            origin(SimpleNamespace(headers=headers), tokens)
    origin(SimpleNamespace(headers={"referer": "http://127.0.0.1/login"}), tokens)


def test_operator_file_is_private_exclusive_and_no_symlink(tmp_path):
    directory = tmp_path / ".local" / "identity"
    path = directory / "token"
    value = random_token()
    token_file(path, value)
    assert path.stat().st_mode & 0o777 == 0o600
    assert directory.stat().st_mode & 0o777 == 0o700
    with pytest.raises(FileExistsError):
        token_file(path, random_token())
    symlink = directory / "link"
    symlink.symlink_to(path)
    with pytest.raises(FileExistsError):
        token_file(symlink, random_token())


def test_missing_auth_configuration_fails_safely():
    with pytest.raises(ConfigurationError) as failure:
        create_app(Settings(environment="test", auth_enabled=True))
    assert str(failure.value) == "Invalid authentication configuration"


def test_disabled_auth_preserves_health_contract(client):
    assert set(client.get("/api/v1/openapi.json").json()["paths"]) == {
        "/health/live",
        "/health/ready",
    }
    assert client.get("/api/v1/auth/me").status_code == 404


def test_enabled_auth_db_unavailable_returns_safe_503(tmp_path, monkeypatch, capsys):
    auth_settings(tmp_path, monkeypatch)
    with TestClient(
        create_app(Settings(environment="test", auth_enabled=True)), base_url="http://127.0.0.1"
    ) as client:
        assert client.get("/health/live").status_code == 200
        schema = client.get("/api/v1/openapi.json").json()
        assert "/api/v1/auth/sessions/{id}" in schema["paths"]
        assert len(schema["paths"]) == 14
        assert "/api/v1/conversations/{id}/messages" in schema["paths"]
        result = client.get("/api/v1/auth/me")
        assert result.status_code == 503 and result.json()["error"]["code"] == "service_unavailable"
        assert result.headers["cache-control"] == "no-store"
    assert "signing_secret" not in capsys.readouterr().err


@pytest.mark.parametrize("change", ["same_key", "weak_key", "origin", "cookie", "blocklist"])
def test_invalid_auth_configuration(tmp_path, change):
    config = auth_settings(tmp_path)
    values = config.model_dump()
    if change == "same_key":
        values["csrf_secret"] = config.signing_secret
    elif change == "weak_key":
        values["signing_secret"] = SecretStr("not-a-random-secret")
    elif change == "origin":
        values["origins"] = ("*",)
    elif change == "cookie":
        values["origins"] = ("http://remote.example.invalid",)
    else:
        values["password_blocklist_sha256"] = "invalid"
    from app.modules.identity.settings import AuthSettings

    with pytest.raises(ValidationError):
        AuthSettings(**values)


def test_chunked_body_limit_precedes_json_and_database(tmp_path, monkeypatch):
    auth_settings(tmp_path, monkeypatch)
    app = create_app(Settings(environment="test", auth_enabled=True))
    with TestClient(app, base_url="http://127.0.0.1") as client:
        response = client.post("/api/v1/auth/activate", content=iter([b"x" * 16384, b"y" * 16385]))
        assert response.status_code == 413
        assert response.json()["error"]["code"] == "request_too_large"
        assert response.headers["cache-control"] == "no-store"
