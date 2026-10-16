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


def create_app(settings: Settings | None = None) -> FastAPI:
    """Construct an isolated app with injectable validated settings and no I/O."""
    config = settings if settings is not None else load_settings()
    logger = make_logger(config.log_level)

    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        handler = logging.StreamHandler()
        handler.setFormatter(SafeJSONFormatter())
        logger.addHandler(handler)
        application.state.started = True
        try:
            logger.info("application_started")
            yield
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
