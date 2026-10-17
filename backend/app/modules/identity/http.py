"""Authentication HTTP boundary: typed bodies, origin/CSRF and committed failures."""

import hmac
import ipaddress
from collections.abc import AsyncIterator
from typing import Annotated
from urllib.parse import urlsplit
from uuid import UUID

import anyio
from fastapi import APIRouter, Depends, Query, Request, Response
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from starlette.responses import JSONResponse

from app.core.errors import error_response
from app.modules.identity.models import AuthRateLimit, AuthSession, User
from app.modules.identity.repository import counter
from app.modules.identity.schemas import (
    Activation,
    Contract,
    CSRFResponse,
    CurrentUser,
    Login,
    SessionList,
    TokenResponse,
)
from app.modules.identity.security import AuthFailure, Tokens
from app.modules.identity.service import Identity

router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])
COOKIE_PATH = "/api/v1/auth"


async def identity(request: Request) -> AsyncIterator[Identity]:
    database = request.app.state.database
    if database.sessions is None:
        raise AuthFailure(503, "service_unavailable")
    async with database.sessions() as db:
        service = Identity(
            db,
            request.app.state.auth_tokens,
            request.app.state.auth_passwords,
            UUID(request.state.request_id),
        )
        try:
            await counter(db, service.tokens, "global_auth", "all", 60, 300)
            await db.commit()
            yield service
            await db.commit()
        except AuthFailure as error:
            # Denials, throttles and especially replay revocation survive HTTP failure.
            try:
                if error.record_audit:
                    await service.event("auth_denied", "denied")
                await db.commit()
            except SQLAlchemyError:
                await db.rollback()
                raise AuthFailure(503, "service_unavailable") from None
            if error.status == 401:
                await anyio.sleep(0.1)
            raise
        except IntegrityError:
            await db.rollback()
            try:
                await service.event("constraint_denied", "denied")
                await db.commit()
            except SQLAlchemyError:
                await db.rollback()
                raise AuthFailure(503, "service_unavailable") from None
            if request.url.path == "/api/v1/auth/activate":
                raise AuthFailure(400, "invitation_invalid") from None
            raise AuthFailure(503, "service_unavailable") from None
        except SQLAlchemyError:
            await db.rollback()
            raise AuthFailure(503, "service_unavailable") from None
        finally:
            with anyio.CancelScope(shield=True):
                await db.close()


Service = Annotated[Identity, Depends(identity, scope="function")]


def origin(request: Request, tokens: Tokens) -> None:
    supplied = request.headers.get("origin")
    if supplied is None:
        referrer = request.headers.get("referer", "")
        try:
            parsed = urlsplit(referrer)
        except ValueError:
            raise AuthFailure(403, "csrf_rejected") from None
        if parsed.username or parsed.password:
            raise AuthFailure(403, "csrf_rejected")
        supplied = f"{parsed.scheme}://{parsed.netloc}"
    if supplied not in tokens.config.origins:
        raise AuthFailure(403, "csrf_rejected")


def client_ip(request: Request, tokens: Tokens) -> str:
    peer = request.client.host if request.client else "unknown"
    value = peer
    if peer in tokens.config.trusted_proxy_addresses:
        value = request.headers.get("x-forwarded-for", peer).split(",")[-1].strip()
    try:
        return str(ipaddress.ip_address(value))
    except ValueError:
        return "unknown"


async def csrf(request: Request, service: Identity) -> None:
    origin(request, service.tokens)
    cookie = request.cookies.get("county_csrf", "")
    header = request.headers.get("x-csrf-token", "")
    if (
        not cookie
        or not header
        or len(cookie) > 4096
        or len(header) > 4096
        or not hmac.compare_digest(cookie.encode(), header.encode())
    ):
        raise AuthFailure(403, "csrf_rejected")
    family = await service.cookie_family(request.cookies.get("county_refresh"))
    service.tokens.context(header, "csrf", str(family.id) if family else "anonymous")


async def bearer(request: Request, service: Identity) -> tuple[User, AuthSession]:
    authorization = request.headers.get("authorization", "")
    if not authorization.startswith("Bearer ") or len(authorization) > 4096:
        raise AuthFailure()
    return await service.authenticate(authorization[7:])


def require_role(user: User, *allowed: str) -> None:
    if user.role not in allowed:
        raise AuthFailure(403, "forbidden")


def cookie(response: Response, service: Identity, name: str, value: str, age: int) -> None:
    response.set_cookie(
        name,
        value,
        max_age=max(0, age),
        path=COOKIE_PATH,
        secure=service.tokens.config.cookie_secure,
        httponly=True,
        samesite="strict",
    )


def clear(response: Response, service: Identity) -> None:
    for name in ("county_refresh", "county_csrf"):
        response.delete_cookie(
            name,
            path=COOKIE_PATH,
            secure=service.tokens.config.cookie_secure,
            httponly=True,
            samesite="strict",
        )


@router.get("/csrf", response_model=CSRFResponse)
async def csrf_token(request: Request, response: Response, service: Service) -> CSRFResponse:
    origin(request, service.tokens)
    await service.admission(client_ip(request, service.tokens), "csrf")
    family = await service.cookie_family(request.cookies.get("county_refresh"))
    lifetime = (
        min(1800, max(1, int((family.expires_at - service.tokens.clock()).total_seconds())))
        if family
        else 1800
    )
    value = service.tokens.sign_context("csrf", str(family.id) if family else "anonymous", lifetime)
    cookie(response, service, "county_csrf", value, lifetime)
    return CSRFResponse(csrf_token=value)


@router.post("/activate", status_code=204)
async def activate(body: Activation, request: Request, service: Service) -> Response:
    await csrf(request, service)
    await service.admission(client_ip(request, service.tokens), "activation")
    await service.activate(body)
    response = Response(status_code=204)
    clear(response, service)
    return response


@router.post("/login", response_model=TokenResponse)
async def login(
    body: Login, request: Request, response: Response, service: Service
) -> TokenResponse:
    await csrf(request, service)
    ip = client_ip(request, service.tokens)
    await service.admission(ip, "login")
    now = service.tokens.clock()
    reservations = [("login_account", body.email, 5), ("login_ip", ip, 20)]
    for dimension, value, limit in reservations:
        await counter(service.db, service.tokens, dimension, value, 900, limit)
    await service.db.commit()  # in-flight failure reservations prevent parallel bypass
    try:
        result, raw, family = await service.login(body)
    except AuthFailure as failure:
        if failure.status == 503:
            for dimension, value, _limit in reservations:
                await service.db.execute(
                    update(AuthRateLimit)
                    .where(
                        AuthRateLimit.dimension == dimension,
                        AuthRateLimit.identifier == service.tokens.pseudonym(value),
                        AuthRateLimit.window == int(now.timestamp()) // 900,
                    )
                    .values(count=AuthRateLimit.count - 1)
                )
        # Retain reserved failures; apply bounded progressive nonblocking delay.
        count = (
            await service.db.execute(
                select(AuthRateLimit.count).where(
                    AuthRateLimit.dimension == "login_account",
                    AuthRateLimit.identifier == service.tokens.pseudonym(body.email),
                    AuthRateLimit.window == int(now.timestamp()) // 900,
                )
            )
        ).scalar_one_or_none()
        await service.db.commit()
        await anyio.sleep(min((count or 1) * 0.05, 0.25))
        raise
    for dimension, value, _limit in reservations:
        await service.db.execute(
            update(AuthRateLimit)
            .where(
                AuthRateLimit.dimension == dimension,
                AuthRateLimit.identifier == service.tokens.pseudonym(value),
                AuthRateLimit.window == int(now.timestamp()) // 900,
            )
            .values(count=AuthRateLimit.count - 1)
        )
    cookie(
        response,
        service,
        "county_refresh",
        raw,
        int((family.expires_at - service.tokens.clock()).total_seconds()),
    )
    return result


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    body: Contract, request: Request, response: Response, service: Service
) -> TokenResponse:
    await csrf(request, service)
    await service.admission(client_ip(request, service.tokens), "refresh")
    family = await service.cookie_family(request.cookies.get("county_refresh"))
    if family:
        await counter(service.db, service.tokens, "refresh_family", str(family.id), 60, 30)
        await service.db.commit()
    result, raw, family = await service.rotate(request.cookies.get("county_refresh"))
    cookie(
        response,
        service,
        "county_refresh",
        raw,
        int((family.expires_at - service.tokens.clock()).total_seconds()),
    )
    return result


@router.post("/logout", status_code=204)
async def logout(body: Contract, request: Request, service: Service) -> Response:
    await csrf(request, service)
    await service.admission(client_ip(request, service.tokens), "mutation")
    await service.logout(request.cookies.get("county_refresh"))
    response = Response(status_code=204)
    clear(response, service)
    return response


@router.post("/logout-all", status_code=204)
async def logout_all(body: Contract, request: Request, service: Service) -> Response:
    await csrf(request, service)
    await service.admission(client_ip(request, service.tokens), "mutation")
    user, _family = await bearer(request, service)
    await service.logout_all(user)
    response = Response(status_code=204)
    clear(response, service)
    return response


@router.get("/me", response_model=CurrentUser)
async def me(request: Request, service: Service) -> CurrentUser:
    user, _family = await bearer(request, service)
    return service.public_user(user)


@router.get("/sessions", response_model=SessionList)
async def sessions(
    request: Request,
    service: Service,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    cursor: Annotated[str | None, Query(max_length=2048)] = None,
) -> SessionList:
    user, family = await bearer(request, service)
    return await service.sessions(user, family, limit, cursor)


@router.delete("/sessions/{session_id}", status_code=204)
async def revoke(session_id: UUID, request: Request, service: Service) -> Response:
    await csrf(request, service)
    await service.admission(client_ip(request, service.tokens), "mutation")
    user, family = await bearer(request, service)
    await service.revoke_session(user, session_id)
    response = Response(status_code=204)
    if session_id == family.id:
        clear(response, service)
    return response


async def auth_error(request: Request, exception: Exception) -> JSONResponse:
    assert isinstance(exception, AuthFailure)
    exc = exception
    response = error_response(request, exc.status, exc.code)
    if exc.status == 401:
        response.headers["WWW-Authenticate"] = "Bearer"
    if exc.retry_after is not None:
        response.headers["Retry-After"] = str(exc.retry_after)
    return response
