import time
from collections.abc import Awaitable, Callable

import structlog
from asgi_correlation_id import CorrelationIdMiddleware
from asgi_correlation_id.context import correlation_id
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response

from app.api.router import api_router
from app.core.config import get_settings
from app.core.logging_config import setup_unified_logging

setup_unified_logging()

logger = structlog.get_logger()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name)
    app.include_router(api_router)

    # Logging middleware must be registered before CorrelationIdMiddleware so that
    # Starlette's reversed build order makes CorrelationIdMiddleware the outermost
    # wrapper — i.e. it executes first and populates correlation_id before we read it.
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

    app.add_middleware(CorrelationIdMiddleware)

    @app.exception_handler(Exception)
    async def global_unhandled_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        logger.exception(
            "Unhandled server error occurred",
            url=str(request.url),
            method=request.method,
            error=str(exc),
        )
        return JSONResponse(
            status_code=500,
            content={
                "detail": (
                    "An internal server error occurred. Our team has been notified."
                ),
                "request_id": correlation_id.get(),
            },
        )

    return app


app = create_app()
