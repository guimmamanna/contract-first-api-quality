"""
Request / response logging middleware for observability.
Logs method, path, status, and latency for every request.
"""

import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("provider.http")


class RequestResponseLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        start = time.perf_counter()
        body_bytes = await request.body()

        logger.info(
            "→ %s %s  headers=%s  body_length=%d",
            request.method,
            request.url.path,
            dict(request.headers),
            len(body_bytes),
        )

        response = await call_next(request)
        elapsed_ms = (time.perf_counter() - start) * 1000

        logger.info(
            "← %s %s  status=%d  elapsed=%.1fms",
            request.method,
            request.url.path,
            response.status_code,
            elapsed_ms,
        )

        return response
