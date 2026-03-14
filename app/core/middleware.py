import time
from collections.abc import Awaitable, Callable

import structlog
from asgi_correlation_id import CorrelationIdMiddleware
from asgi_correlation_id.context import correlation_id
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from slowapi.middleware import SlowAPIMiddleware

from app.core.config import get_settings

logger = structlog.get_logger()


def setup_middleware(app: FastAPI) -> None:
    """Register middlewares for the application."""
    settings = get_settings()

    # Rate Limiting
    app.add_middleware(SlowAPIMiddleware)

    # Security: CORS Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Adjust in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Security: Custom Security Headers Middleware
    @app.middleware("http")
    async def security_headers_middleware(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )
        return response

    # Logging middleware
    @app.middleware("http")
    async def logging_middleware(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=correlation_id.get(),
            method=request.method,
            path=request.url.path,
            client_ip=request.client.host if request.client else None,
            environment=settings.environment,
            app_name=settings.app_name,
        )

        start_time = time.perf_counter()
        response = await call_next(request)
        process_time = time.perf_counter() - start_time

        logger.info(
            "Request completed",
            status_code=response.status_code,
            process_time_ms=round(process_time * 1000, 2),
        )

        return response

    # Correlation ID middleware
    app.add_middleware(
        CorrelationIdMiddleware,
        header_name="X-Request-ID",
        update_request_header=True,
    )
