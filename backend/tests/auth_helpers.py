"""Synthetic auth configuration; generated values never leave test temp directories."""

import base64
import hashlib
import json
import secrets
from pathlib import Path

from app.modules.identity.settings import AuthSettings


def auth_settings(tmp_path: Path, monkeypatch=None) -> AuthSettings:
    content = hashlib.sha256(b"commonly-guessed-synthetic-password").hexdigest().encode() + b"\n"
    blocklist = tmp_path / "passwords.sha256"
    blocklist.write_bytes(content)
    values = {
        "signing_secret": base64.b64encode(secrets.token_bytes(32)).decode(),
        "csrf_secret": base64.b64encode(secrets.token_bytes(32)).decode(),
        "throttle_secret": base64.b64encode(secrets.token_bytes(32)).decode(),
        "issuer": "county-synthetic-test",
        "audience": "county-synthetic-browser",
        "origins": ("http://testserver",),
        "cookie_secure": False,
        "privacy_notice_version": "synthetic-v1",
        "password_blocklist": blocklist,
        "password_blocklist_sha256": hashlib.sha256(content).hexdigest(),
    }
    # TestClient's nonloopback hostname deliberately uses secure cookies instead.
    values["origins"] = ("http://127.0.0.1",)
    config = AuthSettings(**values)
    if monkeypatch:
        for key, value in values.items():
            encoded = json.dumps(value) if isinstance(value, tuple) else str(value)
            monkeypatch.setenv("COUNTY_AUTH_" + key.upper(), encoded)
    return config
