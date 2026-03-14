from typing import Annotated, Any, cast

import httpx
from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from structlog.stdlib import BoundLogger

from app.core.config import Settings
from app.core.dependencies.logging import get_logger
from app.core.dependencies.settings import get_app_settings
from app.db.session import get_db

from .logic import (
    ApiHealthCheck,
    CognitoHealthCheck,
    DatabaseHealthCheck,
    DefaultHealthService,
)


def get_cognito_client_from_state(request: Request) -> Any:
    """Provides a pre-warmed Cognito client from the app state."""
    return request.app.state.cognito_client


def get_http_client_from_state(request: Request) -> httpx.AsyncClient:
    """Provides a pre-warmed HTTP client from the app state."""
    return cast(httpx.AsyncClient, request.app.state.http_client)


async def get_health_service(
    settings: Annotated[Settings, Depends(get_app_settings)],
    logger: Annotated[BoundLogger, Depends(get_logger)],
    cognito_client: Annotated[Any, Depends(get_cognito_client_from_state)],
    http_client: Annotated[httpx.AsyncClient, Depends(get_http_client_from_state)],
    db_session: Annotated[AsyncSession, Depends(get_db)],
) -> DefaultHealthService:
    """Dependency that provides the health service."""
    return DefaultHealthService(
        api_check=ApiHealthCheck(http_client),
        db_check=DatabaseHealthCheck(db_session),
        cognito_check=CognitoHealthCheck(cognito_client, settings.cognito_user_pool_id),
        logger=logger,
    )
