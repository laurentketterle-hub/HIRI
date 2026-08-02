"""Optional API token middleware for admin routes."""

from __future__ import annotations

import os
from collections.abc import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response


def api_token() -> str:
    return (os.environ.get("HIRI_API_TOKEN") or "").strip()


class OptionalTokenMiddleware(BaseHTTPMiddleware):
    """If HIRI_API_TOKEN is set, require Authorization: Bearer <token> on mutating routes."""

    PROTECTED_PREFIXES = (
        "/devices/",  # commands and upserts — also GET detail; we check method
    )

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        token = api_token()
        if not token:
            return await call_next(request)
        # Always allow health/stats/discovery reads without token for dashboards
        path = request.url.path
        method = request.method.upper()
        open_get = method == "GET" and path in {
            "/health",
            "/stats",
            "/devices",
            "/ha/discovery",
            "/adapters",
        }
        open_get_prefix = method == "GET" and path.startswith(("/devices/", "/adapters/"))
        if open_get or open_get_prefix:
            return await call_next(request)
        if method in {"POST", "PUT", "PATCH", "DELETE"}:
            auth = request.headers.get("authorization") or ""
            expected = f"Bearer {token}"
            if auth != expected:
                return JSONResponse({"detail": "unauthorized"}, status_code=401)
        return await call_next(request)
