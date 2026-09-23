"""
Request Logging & Performance Timing Middleware
"""

import time
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("novamart.access")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        start_time = time.perf_counter()
        
        response = await call_next(request)
        
        process_time = time.perf_counter() - start_time
        response.headers["X-Process-Time"] = f"{process_time:.4f}s"
        
        # Don't clutter logs for static assets or health checks
        if not request.url.path.startswith(("/docs", "/openapi.json", "/redoc")):
            logger.info(
                f"{request.method} {request.url.path} -> status={response.status_code} in {process_time:.4f}s"
            )
            
        return response
