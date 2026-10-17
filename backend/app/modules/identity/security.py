"""Bounded password work and purpose-separated signed tokens; no logging."""

import base64
import hashlib
import hmac
import re
import secrets
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

import anyio
import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

from app.modules.identity.settings import AuthSettings


class AuthFailure(Exception):
    def __init__(
        self, status: int = 401, code: str = "invalid_credentials", retry_after: int | None = None
    ):
        self.status = status
        self.code = code
        self.retry_after = retry_after
        self.record_audit = True
        super().__init__(code)


def utcnow() -> datetime:
    return datetime.now(UTC)


def digest(value: str) -> str:
    if not re.fullmatch(r"[A-Za-z0-9_-]{43}", value):
        raise AuthFailure(400, "invitation_invalid")
    raw = base64.urlsafe_b64decode(value + "=")
    if len(raw) != 32 or base64.urlsafe_b64encode(raw).decode().rstrip("=") != value:
        raise AuthFailure(400, "invitation_invalid")
    return hashlib.sha256(value.encode()).hexdigest()


def random_token() -> str:
    return secrets.token_urlsafe(32)


class Passwords:
    def __init__(self, config: AuthSettings):
        data = config.password_blocklist.read_bytes()
        if (
            len(data) > 10 * 1024 * 1024
            or hashlib.sha256(data).hexdigest() != config.password_blocklist_sha256
        ):
            raise ValueError("Invalid offline password blocklist")
        self.blocked = frozenset(data.decode("ascii").splitlines())
        if not self.blocked or any(not re.fullmatch(r"[a-f0-9]{64}", row) for row in self.blocked):
            raise ValueError("Invalid offline password blocklist")
        self.hasher = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=1)
        self.capacity = anyio.CapacityLimiter(config.hash_concurrency)
        self.dummy = self.hasher.hash(secrets.token_urlsafe(48))

    async def run(self, function: Callable[[], Any]) -> Any:
        try:
            self.capacity.acquire_nowait()
        except anyio.WouldBlock:
            raise AuthFailure(503, "service_unavailable") from None
        try:
            return await anyio.to_thread.run_sync(function)
        finally:
            self.capacity.release()

    async def hash(self, password: str) -> str:
        if hashlib.sha256(password.encode()).hexdigest() in self.blocked:
            raise AuthFailure(422, "validation_error")
        return str(await self.run(lambda: self.hasher.hash(password)))

    async def verify(self, password: str, encoded: str | None) -> bool:
        def check() -> bool:
            try:
                return self.hasher.verify(encoded or self.dummy, password)
            except (VerificationError, InvalidHashError):
                return False

        return bool(await self.run(check))


class Tokens:
    def __init__(self, config: AuthSettings, clock: Callable[[], datetime] = utcnow):
        self.config = config
        self.clock = clock
        self.signing = base64.b64decode(config.signing_secret.get_secret_value())
        self.csrf_key = base64.b64decode(config.csrf_secret.get_secret_value())
        self.throttle_key = base64.b64decode(config.throttle_secret.get_secret_value())

    def pseudonym(self, value: str) -> str:
        return hmac.new(self.throttle_key, value.encode(), hashlib.sha256).hexdigest()

    def access(self, user_id: UUID, session_id: UUID, version: int) -> str:
        now = int(self.clock().timestamp())
        return jwt.encode(
            {
                "sub": str(user_id),
                "sid": str(session_id),
                "jti": str(uuid4()),
                "token_version": version,
                "iat": now,
                "exp": now + 900,
                "iss": self.config.issuer,
                "aud": self.config.audience,
            },
            self.signing,
            algorithm="HS256",
        )

    def decode_access(self, token: str) -> dict[str, Any]:
        try:
            claims = jwt.decode(
                token,
                self.signing,
                algorithms=["HS256"],
                issuer=self.config.issuer,
                audience=self.config.audience,
                options={
                    "require": ["sub", "sid", "jti", "token_version", "iat", "exp", "iss", "aud"],
                    "verify_iat": False,
                    "verify_exp": False,
                    "strict_aud": True,
                },
            )
            now = self.clock().timestamp()
            for name in ("iat", "exp", "token_version"):
                if type(claims[name]) is not int:
                    raise ValueError
            if (
                claims["token_version"] < 0
                or claims["iat"] > now + 30
                or not claims["iat"] < claims["exp"] <= claims["iat"] + 900
                or claims["exp"] <= now
            ):
                raise ValueError
            for name in ("sub", "sid", "jti"):
                UUID(claims[name])
            return dict(claims)
        except (jwt.PyJWTError, ValueError, TypeError, KeyError):
            raise AuthFailure() from None

    def sign_context(self, purpose: str, subject: str, lifetime: int, **extra: Any) -> str:
        now = int(self.clock().timestamp())
        return jwt.encode(
            {
                "purpose": purpose,
                "sub": subject,
                "iat": now,
                "exp": now + lifetime,
                "nonce": str(uuid4()),
                **extra,
            },
            self.csrf_key,
            algorithm="HS256",
        )

    def context(self, token: str, purpose: str, subject: str) -> dict[str, Any]:
        try:
            claims = jwt.decode(
                token,
                self.csrf_key,
                algorithms=["HS256"],
                options={
                    "require": ["purpose", "sub", "iat", "exp", "nonce"],
                    "verify_iat": False,
                    "verify_exp": False,
                },
            )
            now = self.clock().timestamp()
            if (
                claims["purpose"] != purpose
                or claims["sub"] != subject
                or type(claims["iat"]) is not int
                or type(claims["exp"]) is not int
                or not claims["iat"] <= now < claims["exp"]
                or claims["exp"] - claims["iat"] > 1800
            ):
                raise ValueError
            return dict(claims)
        except (jwt.PyJWTError, ValueError, TypeError):
            raise AuthFailure(403, "csrf_rejected") from None
