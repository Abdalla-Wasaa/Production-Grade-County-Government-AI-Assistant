"""Process liveness: deliberately independent of infrastructure readiness."""

from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict

router = APIRouter(prefix="/health", tags=["operations"])


class LivenessResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: Literal["ok"] = "ok"


@router.get("/live", response_model=LivenessResponse)
async def live() -> LivenessResponse:
    """Confirm the application can handle a request; perform no dependency checks."""
    return LivenessResponse()
