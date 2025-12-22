"""
Rate limiting middleware for API endpoints.

Supports:
- IP-based rate limiting for unauthenticated requests
- User-based rate limiting for authenticated requests
- Different limits by user role (admin, user)
- Configurable limits per endpoint pattern
"""

import time
from collections import defaultdict
from dataclasses import dataclass
from typing import Callable, Dict, Optional, Tuple

from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings
from app.core.logging import get_logger
from app.core.security import decode_token, verify_token_type

logger = get_logger(__name__)


@dataclass
class RateLimitConfig:
    """Rate limit configuration."""

    requests_per_minute: int = 100
    requests_per_hour: int = 1000


# Default limits by role
DEFAULT_LIMITS = {
    "anonymous": RateLimitConfig(requests_per_minute=60, requests_per_hour=500),
    "user": RateLimitConfig(requests_per_minute=100, requests_per_hour=1000),
    "admin": RateLimitConfig(requests_per_minute=300, requests_per_hour=5000),
}

# Endpoint-specific limits (pattern -> config)
ENDPOINT_LIMITS = {
    "/api/v1/auth/login": RateLimitConfig(requests_per_minute=10, requests_per_hour=50),
    "/api/v1/auth/register": RateLimitConfig(requests_per_minute=5, requests_per_hour=20),
    "/api/v1/auth/forgot-password": RateLimitConfig(requests_per_minute=3, requests_per_hour=10),
}


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware with per-user and per-IP support.

    Features:
    - Authenticated users: Rate limited by user ID
    - Anonymous users: Rate limited by IP address
    - Role-based limits: Different limits for admin, user, anonymous
    - Endpoint-specific limits: Custom limits for sensitive endpoints
    """

    def __init__(
        self,
        app,
        requests_per_minute: int = 100,
        requests_per_hour: int = 1000,
        limits_by_role: Optional[Dict[str, RateLimitConfig]] = None,
        endpoint_limits: Optional[Dict[str, RateLimitConfig]] = None,
    ):
        super().__init__(app)
        self.default_minute = requests_per_minute
        self.default_hour = requests_per_hour
        self.limits_by_role = limits_by_role or DEFAULT_LIMITS
        self.endpoint_limits = endpoint_limits or ENDPOINT_LIMITS

        # Storage: {key: (minute_ts, minute_count, hour_ts, hour_count)}
        self.storage: Dict[str, Tuple[float, int, float, int]] = defaultdict(
            lambda: (0.0, 0, 0.0, 0)
        )

    async def dispatch(self, request: Request, call_next: Callable):
        """Process request with rate limiting."""
        # Skip rate limiting if disabled
        if not settings.RATE_LIMIT_ENABLED:
            return await call_next(request)

        # Skip rate limiting for certain paths
        if self._should_skip(request.url.path):
            return await call_next(request)

        # Get rate limit key and config
        key, config, identifier_type = self._get_rate_limit_key(request)

        # Get endpoint-specific limits if applicable
        endpoint_config = self._get_endpoint_config(request.url.path)
        if endpoint_config:
            config = endpoint_config

        # Check rate limits
        allowed, remaining_minute, remaining_hour = self._check_rate_limit(
            key, config.requests_per_minute, config.requests_per_hour
        )

        if not allowed:
            logger.warning(
                f"Rate limit exceeded: {identifier_type}={key}, "
                f"endpoint={request.url.path}"
            )

            # Log to audit for security monitoring
            try:
                from app.db.session import AsyncSessionLocal
                from app.services.audit_service import (
                    AuditService,
                    EventType,
                    EventAction,
                    Severity,
                    Outcome,
                )

                async with AsyncSessionLocal() as db:
                    audit = AuditService(db)
                    await audit.log(
                        event_type=EventType.SECURITY,
                        event_action=EventAction.RATE_LIMIT,
                        description=f"Rate limit exceeded on {request.url.path}",
                        ip_address=request.client.host if request.client else None,
                        user_agent=request.headers.get("user-agent"),
                        details={
                            "endpoint": request.url.path,
                            "identifier_type": identifier_type,
                            "limit_minute": config.requests_per_minute,
                            "limit_hour": config.requests_per_hour,
                        },
                        severity=Severity.WARNING,
                        outcome=Outcome.FAILURE,
                    )
            except Exception as e:
                logger.error(f"Failed to log rate limit event: {e}")

            retry_after = 60  # Suggest retry after 1 minute
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "Rate limit exceeded",
                    "message": "Too many requests. Please slow down.",
                    "details": {
                        "limit_per_minute": config.requests_per_minute,
                        "limit_per_hour": config.requests_per_hour,
                        "retry_after_seconds": retry_after,
                    },
                },
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit-Minute": str(config.requests_per_minute),
                    "X-RateLimit-Limit-Hour": str(config.requests_per_hour),
                    "X-RateLimit-Remaining-Minute": "0",
                    "X-RateLimit-Remaining-Hour": str(max(0, remaining_hour)),
                },
            )

        # Process request
        response = await call_next(request)

        # Add rate limit headers
        response.headers["X-RateLimit-Limit-Minute"] = str(config.requests_per_minute)
        response.headers["X-RateLimit-Limit-Hour"] = str(config.requests_per_hour)
        response.headers["X-RateLimit-Remaining-Minute"] = str(remaining_minute)
        response.headers["X-RateLimit-Remaining-Hour"] = str(remaining_hour)

        return response

    def _should_skip(self, path: str) -> bool:
        """Check if path should skip rate limiting."""
        skip_paths = [
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/static",
            "/favicon.ico",
        ]
        return any(path.startswith(p) for p in skip_paths)

    def _get_rate_limit_key(
        self, request: Request
    ) -> Tuple[str, RateLimitConfig, str]:
        """
        Get rate limit key and config based on authentication.

        Returns:
            Tuple of (key, config, identifier_type)
        """
        # Try to get user from token
        user_id = None
        user_role = None

        # Check Authorization header
        auth_header = request.headers.get("authorization")
        if auth_header:
            try:
                scheme, token = auth_header.split()
                if scheme.lower() == "bearer":
                    payload = decode_token(token)
                    if payload and verify_token_type(payload, "access"):
                        user_id = payload.get("sub")
                        # Note: Role is not in token, we use default "user" for rate limiting
                        user_role = "user"
            except (ValueError, Exception):
                pass

        # Check API Key header
        if not user_id:
            api_key = request.headers.get("x-api-key")
            if api_key:
                # API key users get "user" role limits
                user_role = "user"
                # Use a hash of the API key as identifier
                import hashlib
                user_id = f"apikey:{hashlib.sha256(api_key.encode()).hexdigest()[:16]}"

        # Get client IP for anonymous users
        client_ip = request.client.host if request.client else "unknown"

        if user_id:
            # Authenticated user - use user ID as key
            config = self.limits_by_role.get(
                user_role or "user",
                self.limits_by_role.get("user", RateLimitConfig())
            )
            return f"user:{user_id}", config, "user"
        else:
            # Anonymous - use IP as key
            config = self.limits_by_role.get(
                "anonymous",
                RateLimitConfig(
                    requests_per_minute=self.default_minute,
                    requests_per_hour=self.default_hour,
                )
            )
            return f"ip:{client_ip}", config, "ip"

    def _get_endpoint_config(self, path: str) -> Optional[RateLimitConfig]:
        """Get endpoint-specific rate limit config."""
        # Exact match
        if path in self.endpoint_limits:
            return self.endpoint_limits[path]

        # Pattern match (simple prefix matching)
        for pattern, config in self.endpoint_limits.items():
            if pattern.endswith("*") and path.startswith(pattern[:-1]):
                return config

        return None

    def _check_rate_limit(
        self,
        key: str,
        limit_minute: int,
        limit_hour: int,
    ) -> Tuple[bool, int, int]:
        """
        Check if request is within rate limits.

        Returns:
            Tuple of (allowed, remaining_minute, remaining_hour)
        """
        now = time.time()
        minute_window = 60
        hour_window = 3600

        # Get current counts
        minute_ts, minute_count, hour_ts, hour_count = self.storage[key]

        # Reset counters if windows expired
        if now - minute_ts > minute_window:
            minute_ts = now
            minute_count = 0

        if now - hour_ts > hour_window:
            hour_ts = now
            hour_count = 0

        # Calculate remaining
        remaining_minute = max(0, limit_minute - minute_count - 1)
        remaining_hour = max(0, limit_hour - hour_count - 1)

        # Check limits
        if minute_count >= limit_minute:
            return False, 0, remaining_hour

        if hour_count >= limit_hour:
            return False, remaining_minute, 0

        # Increment counters
        minute_count += 1
        hour_count += 1

        # Update storage
        self.storage[key] = (minute_ts, minute_count, hour_ts, hour_count)

        # Cleanup old entries periodically
        if len(self.storage) > 10000:
            self._cleanup(now, hour_window)

        return True, remaining_minute, remaining_hour

    def _cleanup(self, now: float, hour_window: float):
        """Remove expired entries from storage."""
        expired_keys = [
            k
            for k, (_, _, hour_ts, _) in self.storage.items()
            if now - hour_ts > hour_window
        ]
        for key in expired_keys:
            del self.storage[key]

    def get_usage(self, key: str) -> Optional[Dict]:
        """Get current usage for a key (for debugging/admin)."""
        if key not in self.storage:
            return None

        minute_ts, minute_count, hour_ts, hour_count = self.storage[key]
        now = time.time()

        return {
            "key": key,
            "minute": {
                "count": minute_count,
                "reset_in": max(0, 60 - (now - minute_ts)),
            },
            "hour": {
                "count": hour_count,
                "reset_in": max(0, 3600 - (now - hour_ts)),
            },
        }
