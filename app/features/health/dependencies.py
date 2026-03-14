from typing import Annotated

import httpx
from fastapi import Depends
from structlog.stdlib import BoundLogger

from app.core.config import Settings
from app.core.dependencies.http import get_http_client
from app.core.dependencies.logging import get_logger
from app.core.dependencies.settings import get_app_settings

from .logic import (
    ApiHealthCheck,
    CognitoHealthCheck,
    DefaultHealthService,
    HealthServiceInterface,
)


async def get_api_health_check() -> ApiHealthCheck:
    """Dependency that provides an ApiHealthCheck."""
    return ApiHealthCheck()


async def get_cognito_health_check(
    settings: Annotated[Settings, Depends(get_app_settings)],
    logger: Annotated[BoundLogger, Depends(get_logger)],
    http_client: Annotated[httpx.AsyncClient, Depends(get_http_client)],
) -> CognitoHealthCheck:
    """Dependency that provides a CognitoHealthCheck."""
    return CognitoHealthCheck(
        settings=settings,
        logger=logger,
        http_client=http_client,
    )


async def get_health_service(
    api_check: Annotated[ApiHealthCheck, Depends(get_api_health_check)],
    cognito_check: Annotated[CognitoHealthCheck, Depends(get_cognito_health_check)],
) -> HealthServiceInterface:
    """Dependency that provides a HealthServiceInterface."""
    return DefaultHealthService(
        checks=[
            api_check,
            cognito_check,
        ]
    )
