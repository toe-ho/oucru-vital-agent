"""Standard error response schema and exception handlers."""

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class AppError(HTTPException):
    """Application-level HTTP error with a machine-readable error_code."""

    def __init__(self, status_code: int, error_code: str, detail: str = "") -> None:
        super().__init__(status_code=status_code, detail=detail)
        self.error_code = error_code


def _error_body(error: str, detail: str, request_id: str) -> dict:
    return {"error": error, "detail": detail, "request_id": request_id}


async def _app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=_error_body(
            exc.error_code,
            exc.detail or "",
            request.headers.get("x-request-id", ""),
        ),
    )


async def _validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content=_error_body(
            "ValidationError",
            str(exc.errors()),
            request.headers.get("x-request-id", ""),
        ),
    )


async def _unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content=_error_body(
            "InternalServerError",
            "An unexpected error occurred.",
            request.headers.get("x-request-id", ""),
        ),
    )


def register_error_handlers(app: FastAPI) -> None:
    """Register all error handlers on the FastAPI application."""
    app.add_exception_handler(AppError, _app_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, _validation_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, _unhandled_error_handler)  # type: ignore[arg-type]
