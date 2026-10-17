"""Application composition. Use Uvicorn's --factory flag; no global app instance."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.health import router as health_router
from app.api.v1 import router as api_router
from app.core.config import Settings, load_settings
from app.core.errors import install_error_handlers
from app.core.logging import SafeJSONFormatter, make_logger
from app.core.middleware import (
    ErrorBoundaryMiddleware,
    LocalCORSMiddleware,
    RequestContextMiddleware,
)
from app.db.session import Database


def create_app(settings: Settings | None = None) -> FastAPI:
    """Construct an isolated app with injectable validated settings and no I/O."""
    config = settings if settings is not None else load_settings()
    logger = make_logger(config.log_level)
    auth_config = None
    if config.auth_enabled:
        from pydantic import ValidationError

        from app.core.config import ConfigurationError
        from app.modules.identity.settings import AuthSettings

        try:
            auth_config = AuthSettings()
        except (ValidationError, ValueError):
            raise ConfigurationError("Invalid authentication configuration") from None

    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        handler = logging.StreamHandler()
        handler.setFormatter(SafeJSONFormatter())
        logger.addHandler(handler)
        database: Database | None = None
        try:
            database = Database(config, logger)
            application.state.database = database
            if auth_config is not None:
                from app.modules.identity.security import Passwords, Tokens

                try:
                    application.state.auth_tokens = Tokens(auth_config)
                    application.state.auth_passwords = Passwords(auth_config)
                except (ValueError, OSError):
                    from app.core.config import ConfigurationError

                    raise ConfigurationError("Invalid authentication resources") from None
            application.state.started = True
            logger.info("application_started")
            yield
        finally:
            try:
                if database is not None:
                    await database.dispose()
            finally:
                application.state.started = False
                logger.info("application_stopped")
                logger.removeHandler(handler)
                handler.close()

    app = FastAPI(
        title="County Government AI Assistant",
        version="0.1.0",
        debug=False,
        lifespan=lifespan,
        docs_url=None,
        redoc_url=None,
        openapi_url="/api/v1/openapi.json",
        redirect_slashes=False,
    )
    app.state.settings = config
    app.state.logger = logger
    app.state.started = False
    install_error_handlers(app)
    app.include_router(health_router)
    app.include_router(api_router)
    if auth_config is not None:
        from app.modules.identity.body_limit import AuthBodyLimit
        from app.modules.identity.http import auth_error
        from app.modules.identity.http import router as auth_router
        from app.modules.identity.security import AuthFailure

        app.include_router(auth_router)
        app.add_exception_handler(AuthFailure, auth_error)
        app.add_middleware(AuthBodyLimit)
    # Starlette wraps later-added middleware around earlier layers. Error handling
    # is inside CORS; request metadata wraps both, including preflight responses.
    app.add_middleware(ErrorBoundaryMiddleware, logger=logger)
    app.add_middleware(
        LocalCORSMiddleware,
        allow_origins=list(config.cors_origins),
        allow_credentials=False,
        allow_methods=["GET"],
        allow_headers=["Accept", "Content-Type"],
        expose_headers=["X-Request-ID"],
    )
    app.add_middleware(RequestContextMiddleware, logger=logger)
    return app
