"""
Custom Exceptions for WAHA FastAPI Application
"""

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from api.core.config import settings


class WAHAException(Exception):
    """Base WAHA exception"""

    def __init__(
        self,
        message: str,
        code: str = None,
        status_code: int = 500,
        details: dict = None
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class WAHAConnectionException(WAHAException):
    """WAHA connection exception"""

    def __init__(self, message: str, details: dict = None):
        super().__init__(
            message=message,
            code="WAHA_CONNECTION_ERROR",
            status_code=503,
            details=details
        )


class WAHAAuthenticationException(WAHAException):
    """WAHA authentication exception"""

    def __init__(self, message: str, details: dict = None):
        super().__init__(
            message=message,
            code="AUTHENTICATION_ERROR",
            status_code=401,
            details=details
        )


class WAHAValidationException(WAHAException):
    """WAHA validation exception"""

    def __init__(self, message: str, details: dict = None):
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            status_code=400,
            details=details
        )


class WAHARateLimitException(WAHAException):
    """WAHA rate limit exception"""

    def __init__(self, message: str, retry_after: int = None, details: dict = None):
        super().__init__(
            message=message,
            code="RATE_LIMIT_EXCEEDED",
            status_code=429,
            details=details
        )
        self.retry_after = retry_after


class WAHASessionException(WAHAException):
    """WAHA session exception"""

    def __init__(self, message: str, session_status: str = None, details: dict = None):
        super().__init__(
            message=message,
            code="SESSION_ERROR",
            status_code=422,
            details=details
        )
        self.session_status = session_status


async def waha_exception_handler(request: Request, exc: WAHAException) -> JSONResponse:
    """Global WAHA exception handler"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.message,
            "code": exc.code,
            "details": exc.details if settings.DEBUG else None,
            "metadata": {
                "timestamp": settings.get_current_time(),
                "path": str(request.url.path),
                "method": request.method,
                "request_id": getattr(request.state, "request_id", None)
            }
        }
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """HTTP exception handler"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.detail,
            "code": f"HTTP_{exc.status_code}",
            "metadata": {
                "timestamp": settings.get_current_time(),
                "path": str(request.url.path),
                "method": request.method,
                "request_id": getattr(request.state, "request_id", None)
            }
        }
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Validation exception handler"""
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(x) for x in error["loc"]),
            "message": error["msg"],
            "type": error["type"],
            "input": error["input"] if settings.DEBUG else None
        })

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error": "Validation failed",
            "code": "VALIDATION_ERROR",
            "details": {
                "errors": errors,
                "error_count": len(errors)
            },
            "metadata": {
                "timestamp": settings.get_current_time(),
                "path": str(request.url.path),
                "method": request.method,
                "request_id": getattr(request.state, "request_id", None)
            }
        }
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """General exception handler"""
    import traceback

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": "Internal server error",
            "code": "INTERNAL_ERROR",
            "details": {
                "error": str(exc),
                "traceback": traceback.format_exc() if settings.DEBUG else None
            },
            "metadata": {
                "timestamp": settings.get_current_time(),
                "path": str(request.url.path),
                "method": request.method,
                "request_id": getattr(request.state, "request_id", None)
            }
        }
    )


def setup_exception_handlers(app):
    """Setup exception handlers for FastAPI app"""
    app.add_exception_handler(WAHAException, waha_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)