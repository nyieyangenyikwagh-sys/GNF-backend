import logging
from typing import Any

from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.request_context import correlation_id


logger = logging.getLogger(__name__)


def error_body(code: str, message: str, details: Any = None) -> dict:
    return {
        "error": {"code": code, "message": message, "details": details},
        "correlation_id": correlation_id(),
    }


async def validation_error_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    details = [
        {
            "field": ".".join(str(part) for part in error["loc"] if part != "body"),
            "message": error["msg"],
            "type": error["type"],
        }
        for error in exc.errors()
    ]
    malformed_json = any(error["type"] == "json_invalid" for error in exc.errors())
    return JSONResponse(error_body("MALFORMED_JSON" if malformed_json else "VALIDATION_ERROR", "Malformed JSON" if malformed_json else "Request validation failed", details), status_code=400 if malformed_json else 422)


async def http_error_handler(_: Request, exc: HTTPException) -> JSONResponse:
    if isinstance(exc.detail, dict):
        code = str(exc.detail.get("code", "HTTP_ERROR"))
        message = str(exc.detail.get("message", "Request failed"))
        details = exc.detail.get("details")
    else:
        code = {
            400: "BAD_REQUEST",
            401: "UNAUTHORIZED",
            403: "FORBIDDEN",
            404: "NOT_FOUND",
            409: "CONFLICT",
            413: "REQUEST_TOO_LARGE",
        }.get(exc.status_code, "HTTP_ERROR")
        message = str(exc.detail)
        details = None
    return JSONResponse(error_body(code, message, details), status_code=exc.status_code, headers=exc.headers)


async def server_error_handler(_: Request, exc: Exception) -> JSONResponse:
    logger.exception("unhandled_request_error", exc_info=exc)
    return JSONResponse(error_body("INTERNAL_ERROR", "The request could not be completed"), status_code=500)
