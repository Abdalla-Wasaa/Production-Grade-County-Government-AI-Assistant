"""Safe HTTP error contracts; raw input and exception detail never leave this boundary."""

from typing import Literal

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, ConfigDict, Field
from starlette.exceptions import HTTPException
from starlette.responses import JSONResponse


class ErrorDetail(BaseModel):
    model_config = ConfigDict(extra="forbid")
    field: str
    code: Literal["invalid"] = "invalid"


class ErrorBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    code: str
    message: str
    request_id: str
    details: list[ErrorDetail] = Field(default_factory=list)


class ErrorResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    error: ErrorBody


MESSAGES = {
    "en": {
        "not_found": "Resource not found.",
        "method_not_allowed": "Method not allowed.",
        "validation_error": "Check the request fields.",
        "http_error": "The request could not be completed.",
        "internal_error": "An unexpected error occurred.",
        "cors_rejected": "Cross-origin request not allowed.",
    },
    "sw": {
        "not_found": "Rasilimali haikupatikana.",
        "method_not_allowed": "Njia hii hairuhusiwi.",
        "validation_error": "Kagua sehemu za ombi.",
        "http_error": "Ombi halikuweza kukamilishwa.",
        "internal_error": "Hitilafu isiyotarajiwa imetokea.",
        "cors_rejected": "Ombi kutoka chanzo hiki haliruhusiwi.",
    },
}


def error_response(request: Request, status: int, code: str) -> JSONResponse:
    """Use fixed localized messages; do not echo exception or request values."""
    language = "sw" if request.headers.get("accept-language", "").lower() == "sw" else "en"
    body = ErrorResponse(
        error=ErrorBody(
            code=code,
            message=MESSAGES[language][code],
            request_id=request.state.request_id,
            # Detailed field paths can contain attacker-controlled dictionary keys.
            details=[ErrorDetail(field="request")] if status == 422 else [],
        )
    )
    headers = {"Allow": "GET"} if status == 405 and request.url.path == "/health/live" else {}
    return JSONResponse(body.model_dump(), status_code=status, headers=headers)


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(HTTPException)
    async def http_error(request: Request, exc: HTTPException) -> JSONResponse:
        code = {404: "not_found", 405: "method_not_allowed"}.get(exc.status_code, "http_error")
        return error_response(request, exc.status_code, code)

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, _exc: RequestValidationError) -> JSONResponse:
        return error_response(request, 422, "validation_error")
