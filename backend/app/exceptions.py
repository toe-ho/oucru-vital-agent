from __future__ import annotations

from fastapi import Request
from fastapi.responses import JSONResponse


class AppException(Exception):
    def __init__(self, status_code: int, error: str, detail: str) -> None:
        self.status_code = status_code
        self.error = error
        self.detail = detail


class NotFoundError(AppException):
    def __init__(self, detail: str) -> None:
        super().__init__(404, "NotFound", detail)


class ValidationError(AppException):
    def __init__(self, detail: str) -> None:
        super().__init__(400, "BadRequest", detail)


class ForbiddenError(AppException):
    def __init__(self, detail: str = "Insufficient permissions") -> None:
        super().__init__(403, "Forbidden", detail)


class UnauthorizedError(AppException):
    def __init__(self, detail: str = "Authentication required") -> None:
        super().__init__(401, "Unauthorized", detail)


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    request_id = getattr(request.state, "request_id", "unknown")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.error, "detail": exc.detail, "request_id": request_id},
    )
