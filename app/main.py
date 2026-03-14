import time
from collections.abc import AsyncGenerator, Awaitable, Callable
from contextlib import asynccontextmanager
from typing import Any

import boto3
import httpx
import structlog
from asgi_correlation_id import CorrelationIdMiddleware
from asgi_correlation_id.context import correlation_id
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response

from app.api.router import router as api_router
from app.core.config import get_settings
from app.core.exceptions.base_app_exception import BaseAppException
from app.core.logging_config import setup_unified_logging

setup_unified_logging()

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Lifecycle manager for resources (clients, connections, etc.)
    Everything inside the yield is available during app runtime.
    """
    settings = get_settings()

    # Initialize long-lived clients (only if not already mocked/set)
    if not hasattr(app.state, "http_client"):
        app.state.http_client = httpx.AsyncClient(timeout=10.0)

    if not hasattr(app.state, "cognito_client"):
        app.state.cognito_client = boto3.client(
            "cognito-idp",
            region_name=settings.cognito_region,
        )

    yield

    # Cleanup at shutdown
    if hasattr(app.state, "http_client"):
        await app.state.http_client.aclose()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, lifespan=lifespan)
    app.include_router(api_router, prefix="/api")

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
            environment=settings.environment,
            app_name=settings.app_name,
        )

        start_time = time.perf_counter()
        # In tests using TestClient, request.app is the app instance
        response = await call_next(request)
        process_time = time.perf_counter() - start_time

        logger.info(
            "Request completed",
            status_code=response.status_code,
            process_time_ms=round(process_time * 1000, 2),
        )

        return response

    app.add_middleware(CorrelationIdMiddleware)

    @app.exception_handler(BaseAppException)
    async def base_app_exception_handler(
        request: Request, exc: BaseAppException
    ) -> JSONResponse:
        content: dict[str, Any] = {"detail": exc.message}
        if exc.error_code:
            content["error_code"] = exc.error_code
        if exc.data:
            content["data"] = exc.data

        return JSONResponse(
            status_code=exc.status_code,
            content=content,
        )

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
