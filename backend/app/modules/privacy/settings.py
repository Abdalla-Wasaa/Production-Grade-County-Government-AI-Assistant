"""Secret-file-only maintenance configuration; no .env discovery or JWT signing key."""

import base64
import os
import stat
from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.config import validate_database_url


def private_value(path: Path) -> str:
    if any(parent.is_symlink() for parent in (path, *path.parents)):
        raise ValueError("Symlink secret path")
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        info = os.fstat(descriptor)
        if not stat.S_ISREG(info.st_mode) or info.st_mode & 0o022 or info.st_size > 8192:
            raise ValueError("Invalid secret file")
        with os.fdopen(descriptor, closefd=False) as stream:
            value = stream.read(8193).strip()
        if not value or len(value) > 8192 or "\x00" in value:
            raise ValueError("Invalid secret value")
        return value
    finally:
        os.close(descriptor)


class PrivacySettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="COUNTY_PRIVACY_", env_file=None, extra="forbid", hide_input_in_errors=True
    )
    database_url_file: Path
    audit_key_file: Path

    def secrets(self) -> tuple[SecretStr, bytes]:
        url = SecretStr(private_value(self.database_url_file))
        validate_database_url(url)
        # Must be the existing authentication throttle/HMAC key, not a new key:
        # holds must correlate existing pseudonymous subject audits without PII.
        key = base64.b64decode(private_value(self.audit_key_file), validate=True)
        if len(key) < 32 or len(set(key)) < 16:
            raise ValueError("Invalid audit key")
        return url, key
