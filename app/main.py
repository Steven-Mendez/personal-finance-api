from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

import boto3
import httpx
import structlog
from fastapi import FastAPI, Request, Response
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api.router import router as api_router
from app.core.config import get_settings
from app.core.exceptions.handlers import setup_exception_handlers
from app.core.logging_config import setup_unified_logging
from app.core.middleware import setup_middleware
from app.core.observability import setup_observability
from app.core.rate_limit import limiter
from app.core.schemas.responses import ResponseEnvelope
from app.db.session import engine

# Initialize logging as early as possible
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

    # Close DB engine
    await engine.dispose()


def create_app() -> FastAPI:
    """Application factory to create and configure the FastAPI instance."""
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        description=(
            "A robust foundation for a Personal Finance Tracking and Budgeting API."
        ),
        version="1.0.0",
        contact={
            "name": "Personal Finance API Support",
            "email": "support@example.com",
        },
        license_info={
            "name": "Proprietary",
        },
        openapi_tags=[
            {
                "name": "v1",
                "description": "Stable Version 1.0 of the API",
            },
            {
                "name": "identity",
                "description": "User authentication and management",
            },
            {
                "name": "health",
                "description": "System health and dependency status",
            },
        ],
        responses={
            400: {"model": ResponseEnvelope[None], "description": "Bad Request"},
            401: {"model": ResponseEnvelope[None], "description": "Unauthorized"},
            403: {"model": ResponseEnvelope[None], "description": "Forbidden"},
            404: {"model": ResponseEnvelope[None], "description": "Not Found"},
            409: {"model": ResponseEnvelope[None], "description": "Conflict"},
            422: {"model": ResponseEnvelope[None], "description": "Validation Error"},
            500: {
                "model": ResponseEnvelope[None],
                "description": "Internal Server Error",
            },
        },
        lifespan=lifespan,
    )

    # Initialize rate limiting state
    app.state.limiter = limiter

    @app.exception_handler(RateLimitExceeded)
    def rate_limit_exceeded_handler(request: Request, exc: Any) -> Response:
        """Standard handler for rate limit exceeded errors."""
        return _rate_limit_exceeded_handler(request, exc)

    # Register Middlewares
    setup_middleware(app)

    # Register Observability (Metrics)
    setup_observability(app)

    # Register Exception Handlers
    setup_exception_handlers(app)

    # Include Versioned API Router
    app.include_router(api_router, prefix="/api")

    return app


app = create_app()
