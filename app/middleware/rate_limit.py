import time
from collections import defaultdict

from fastapi import HTTPException, Request, status
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import settings


class RateLimitMiddleware(BaseHTTPMiddleware):
    instances: list["RateLimitMiddleware"] = []

    def __init__(self, app):
        super().__init__(app)
        self.auth_requests: dict[str, list[float]] = defaultdict(list)
        self.content_requests: dict[str, list[float]] = defaultdict(list)
        RateLimitMiddleware.instances.append(self)

    @classmethod
    def reset(cls):
        for inst in cls.instances:
            inst.auth_requests.clear()
            inst.content_requests.clear()

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        path = request.url.path

        if self._is_auth_endpoint(path):
            self._check_rate_limit(client_ip, self.auth_requests, settings.rate_limit_auth_per_minute)
        elif self._is_content_endpoint(path) and request.method in ("POST", "PUT", "PATCH", "DELETE"):
            self._check_rate_limit(client_ip, self.content_requests, settings.rate_limit_content_per_minute)

        response = await call_next(request)
        return response

    def _is_auth_endpoint(self, path: str) -> bool:
        return path.startswith("/api/v1/auth/")

    def _is_content_endpoint(self, path: str) -> bool:
        content_paths = ("/api/v1/events", "/api/v1/posts", "/api/v1/comments")
        return any(path.startswith(p) for p in content_paths)

    def _check_rate_limit(self, key: str, store: dict, limit: int):
        now = time.time()
        window_start = now - 60
        store[key] = [t for t in store[key] if t > window_start]
        if len(store[key]) >= limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Max {limit} requests per minute.",
            )
        store[key].append(now)
