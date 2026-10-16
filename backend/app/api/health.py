"""Process liveness: deliberately independent of infrastructure readiness."""

from typing import Literal

from fastapi import APIRouter, Request
from pydantic import BaseModel, ConfigDict
from starlette.responses import JSONResponse

from app.core.errors import ErrorResponse, error_response
from app.db.readiness import is_ready

router = APIRouter(prefix="/health", tags=["operations"])


class LivenessResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: Literal["ok"] = "ok"


@router.get("/live", response_model=LivenessResponse)
async def live() -> LivenessResponse:
    """Confirm the application can handle a request; perform no dependency checks."""
    return LivenessResponse()


@router.get("/ready", response_model=LivenessResponse, responses={503: {"model": ErrorResponse}})
async def ready(request: Request) -> LivenessResponse | JSONResponse:
    """Check reachability and revision without applying migrations."""
    if await is_ready(
        request.app.state.database, request.app.state.settings.db_readiness_timeout_seconds
    ):
        return LivenessResponse()
    return error_response(request, 503, "service_unavailable")
