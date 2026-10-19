"""Prepared policy/schema tests; execute only after the privacy exposure authorization."""

import base64
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.modules.privacy.schemas import (
    DeleteAccountCommand,
    HoldCommand,
    acknowledgement_target,
    daily_target,
)
from app.modules.privacy.service import Privacy, operator_digest
from app.modules.privacy.settings import PrivacySettings, private_value


@pytest.mark.parametrize(
    ("now", "expected"),
    [
        ("2026-10-19T22:59:00+00:00", "2026-10-18T23:00:00+00:00"),
        ("2026-10-19T23:00:00+00:00", "2026-10-19T23:00:00+00:00"),
        ("2026-10-20T00:00:00+00:00", "2026-10-19T23:00:00+00:00"),
        ("2027-01-01T00:00:00+00:00", "2026-12-31T23:00:00+00:00"),
    ],
)
def test_nairobi_daily_boundary(now, expected):
    assert daily_target(datetime.fromisoformat(now)) == datetime.fromisoformat(expected)


def test_naive_clock_is_rejected():
    with pytest.raises(ValueError, match="Timezone required"):
        daily_target(datetime(2026, 10, 19))


@pytest.mark.parametrize(("day", "due"), [(16, 20), (17, 20), (18, 20), (19, 21)])
def test_synthetic_two_working_day_acknowledgement(day, due):
    assert acknowledgement_target(datetime(2026, 10, day, 8, tzinfo=UTC)).day == due


@pytest.mark.parametrize(
    "change",
    [
        {"scope": "everyone"},
        {"reason": "unbounded personal content"},
        {"target_id": "invalid"},
        {"content": "forbidden"},
        {"case_ref": "email@example.invalid"},
    ],
)
def test_hold_contract_bounds_and_no_content_fields(change):
    body = dict(id=uuid4(), scope="account", target_id=uuid4(), reason="incident", case_ref=uuid4())
    body.update(change)
    with pytest.raises(ValidationError):
        HoldCommand.model_validate(body)


@pytest.mark.parametrize("verified", [False, None, "yes"])
def test_deletion_requires_explicit_actual_verification(verified):
    with pytest.raises(ValidationError):
        DeleteAccountCommand.model_validate(
            dict(id=uuid4(), user_id=uuid4(), verification_ref=uuid4(), verified=verified)
        )


def test_caller_cannot_supply_an_operator_identity():
    with pytest.raises(ValidationError):
        DeleteAccountCommand.model_validate(
            dict(
                id=uuid4(),
                user_id=uuid4(),
                verification_ref=uuid4(),
                verified=True,
                operator="claimed-admin",
            )
        )


def test_secret_file_is_not_echoed_and_is_not_discovered(tmp_path):
    secret = tmp_path / "secret"
    secret.write_text("synthetic-private-marker")
    secret.chmod(0o600)
    assert private_value(secret) == "synthetic-private-marker"
    secret.chmod(0o666)
    with pytest.raises(ValueError, match="Invalid secret file"):
        private_value(secret)
    with pytest.raises(ValidationError):
        PrivacySettings()


def test_symlink_secret_is_rejected(tmp_path):
    source = tmp_path / "source"
    source.write_text("synthetic-private-marker")
    link = tmp_path / "link"
    link.symlink_to(source)
    with pytest.raises(ValueError, match="Symlink secret path"):
        private_value(link)


def test_secret_config_has_no_jwt_signing_dependency(tmp_path):
    db = tmp_path / "url"
    key = tmp_path / "key"
    db.write_text("postgresql+psycopg://synthetic@127.0.0.1/synthetic")
    key.write_text(base64.b64encode(bytes(range(32))).decode())
    db.chmod(0o600)
    key.chmod(0o600)
    config = PrivacySettings(database_url_file=db, audit_key_file=key)
    url, decoded = config.secrets()
    assert "synthetic@" not in repr(url)
    assert len(decoded) == 32
    assert "signing" not in PrivacySettings.model_fields


def test_audit_values_are_bounded_pseudonyms():
    # Pure operation does not connect or authorize; every service mutation checks DB identity.
    store = Privacy(None, bytes(range(32)))  # type: ignore[arg-type]
    assert len(store.pseudonym("synthetic-user")) == 64
    assert store.pseudonym("synthetic-user") != store.pseudonym("other-user")
    assert len(operator_digest("synthetic-operator")) == 64
