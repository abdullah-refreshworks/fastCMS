"""
Rate limiting middleware for API endpoints.
"""

import time
from collections import defaultdict
from typing import Callable, Dict, Tuple

from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple in-memory rate limiting middleware."""

    def __init__(self, app, requests_per_minute: int = 100, requests_per_hour: int = 1000):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        # Storage: {ip: [(timestamp, count_minute), (timestamp, count_hour)]}
        self.storage: Dict[str, Tuple[float, int, float, int]] = defaultdict(
            lambda: (0.0, 0, 0.0, 0)
        )

    async def dispatch(self, request: Request, call_next: Callable):
        """Process request with rate limiting."""
        # Skip rate limiting if disabled
        if not settings.RATE_LIMIT_ENABLED:
            return await call_next(request)

        # Get client IP
        client_ip = request.client.host if request.client else "unknown"

        # Check rate limits
        if not self._check_rate_limit(client_ip):
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "Rate limit exceeded",
                    "details": f"Maximum {self.requests_per_minute} requests per minute",
                },
            )

        # Process request
        response = await call_next(request)

        # Add rate limit headers
        response.headers["X-RateLimit-Limit-Minute"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Limit-Hour"] = str(self.requests_per_hour)

        return response

    def _check_rate_limit(self, client_ip: str) -> bool:
        """
        Check if client is within rate limits.

        Returns:
            True if request is allowed, False if rate limit exceeded
        """
        now = time.time()
        minute_window = 60
        hour_window = 3600

        # Get current counts
        minute_ts, minute_count, hour_ts, hour_count = self.storage[client_ip]

        # Reset counters if windows expired
        if now - minute_ts > minute_window:
            minute_ts = now
            minute_count = 0

        if now - hour_ts > hour_window:
            hour_ts = now
            hour_count = 0

        # Check limits
        if minute_count >= self.requests_per_minute:
            return False

        if hour_count >= self.requests_per_hour:
            return False

        # Increment counters
        minute_count += 1
        hour_count += 1

        # Update storage
        self.storage[client_ip] = (minute_ts, minute_count, hour_ts, hour_count)

        # Cleanup old entries periodically
        if len(self.storage) > 10000:
            self._cleanup(now, hour_window)

        return True

    def _cleanup(self, now: float, hour_window: float):
        """Remove expired entries from storage."""
        expired_keys = [
            ip
            for ip, (_, _, hour_ts, _) in self.storage.items()
            if now - hour_ts > hour_window
        ]
        for key in expired_keys:
            del self.storage[key]
