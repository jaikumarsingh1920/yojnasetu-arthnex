import time
import logging
from collections import defaultdict
from typing import Dict, List, Tuple
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
from fastapi import status

from app.core.config import settings
from app.core.errors import build_error_response

logger = logging.getLogger("yojnasetu.ratelimit")

# Endpoint rules: path_prefix -> (max_requests, window_seconds)
RATE_LIMIT_RULES: List[Tuple[str, int, int]] = [
    ("/api/v1/auth/login", 10, 60),
    ("/api/v1/auth/register", 10, 60),
    ("/api/v1/ai/profile/extract", 15, 60),
    ("/api/v1/ai/recommend", 15, 60),
    ("/api/v1/ai/chat", 60, 60),
    ("/api/v1/ai/schemes/", 60, 60),
    ("/api/v1/financial-health/assess", 30, 60),
    ("/email", 5, 60),
]


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.requests_store: Dict[str, List[float]] = defaultdict(list)

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        path = request.url.path
        method = request.method
        client_ip = request.client.host if request.client else "unknown"

        # Allow automated tests and local demo environment to skip rate limiting unless explicitly testing it
        test_force_rate_limit = request.headers.get("X-Test-Rate-Limit") == "1"
        if (settings.ENV in ("testing", "development") and client_ip in ("127.0.0.1", "localhost", "testclient")) and not test_force_rate_limit:
            return await call_next(request)

        if method in ("POST", "PUT"):
            for prefix, max_reqs, window_sec in RATE_LIMIT_RULES:
                matches = path.startswith(prefix) or (prefix == "/email" and path.endswith("/email"))
                if matches:
                    key = f"{client_ip}:{prefix}"
                    now = time.time()
                    cutoff = now - window_sec

                    # Filter out old timestamps
                    self.requests_store[key] = [t for t in self.requests_store[key] if t > cutoff]

                    if len(self.requests_store[key]) >= max_reqs:
                        logger.warning(f"Rate limit exceeded for IP {client_ip} on {path}")
                        return build_error_response(
                            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                            code="TOO_MANY_REQUESTS",
                            message=f"Too many requests to {prefix}. Please wait a minute before retrying."
                        )

                    self.requests_store[key].append(now)
                    break

        return await call_next(request)

