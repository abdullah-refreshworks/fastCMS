"""Custom middleware"""
import time
import uuid
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.logging import get_logger
from app.core.readonly import is_readonly, get_readonly_reason

logger = get_logger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log all requests"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # Record start time
        start_time = time.time()

        # Get user if authenticated
        user_id = None
        if hasattr(request.state, "user"):
            user_id = request.state.user.id

        # Process request
        response = await call_next(request)

        # Calculate duration
        duration_ms = int((time.time() - start_time) * 1000)

        # Log to database (async, don't block response)
        try:
            from app.services.settings_service import SettingsService
            from app.db.session import AsyncSessionLocal

            async with AsyncSessionLocal() as db:
                settings = SettingsService(db)
                log_enabled = await settings.get("logs.enabled", True)

                if log_enabled:
                    from app.services.log_service import LogService

                    log_service = LogService(db)
                    await log_service.create_log(
                        method=request.method,
                        url=str(request.url),
                        status_code=response.status_code,
                        duration_ms=duration_ms,
                        user_agent=request.headers.get("user-agent"),
                        ip_address=request.client.host if request.client else None,
                        auth_user_id=user_id,
                    )
        except Exception as e:
            logger.error(f"Failed to log request: {str(e)}")

        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id

        return response


class ReadOnlyMiddleware(BaseHTTPMiddleware):
    """Middleware to enforce read-only mode"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Check if read-only mode is enabled
        if is_readonly():
            # Allow read operations
            if request.method in ["GET", "HEAD", "OPTIONS"]:
                return await call_next(request)

            # Block write operations
            from fastapi.responses import JSONResponse

            return JSONResponse(
                status_code=503,
                content={
                    "error": "Service temporarily read-only",
                    "reason": get_readonly_reason(),
                    "detail": "System is in maintenance mode. Only read operations are allowed.",
                },
            )

        return await call_next(request)
