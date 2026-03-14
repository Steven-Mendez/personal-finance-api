from typing import Annotated, Any

import httpx
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from structlog.stdlib import BoundLogger

from app.core.config import Settings
from app.core.dependencies.cognito import get_cognito_client
from app.core.dependencies.http import get_http_client
from app.core.dependencies.logging import get_logger
from app.core.dependencies.settings import get_app_settings
from app.db.session import get_db

from .logic import (
    ApiHealthCheck,
    CognitoHealthCheck,
    DatabaseHealthCheck,
    DefaultHealthService,
)


async def get_health_service(
    settings: Annotated[Settings, Depends(get_app_settings)],
    logger: Annotated[BoundLogger, Depends(get_logger)],
    cognito_client: Annotated[Any, Depends(get_cognito_client)],
    http_client: Annotated[httpx.AsyncClient, Depends(get_http_client)],
    db_session: Annotated[AsyncSession, Depends(get_db)],
) -> DefaultHealthService:
    """Dependency that provides the health service."""
    return DefaultHealthService(
        api_check=ApiHealthCheck(http_client),
        db_check=DatabaseHealthCheck(db_session),
        cognito_check=CognitoHealthCheck(cognito_client, settings.cognito_user_pool_id),
        logger=logger,
        version=settings.commit_sha,
    )
