from typing import Annotated, Any, AsyncGenerator

import boto3
import httpx
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from structlog.stdlib import BoundLogger

from app.api.dependencies.logging import get_logger
from app.api.dependencies.settings import get_app_settings
from app.core.config import Settings
from app.services.auth import Authenticator, TokenVerifier, UserManager
from app.services.cognito.cognito_authenticator import CognitoAuthenticator
from app.services.cognito.cognito_token_verifier import CognitoTokenVerifier
from app.services.cognito.cognito_user_manager import CognitoUserManager

reusable_oauth2 = HTTPBearer()


async def get_http_client() -> AsyncGenerator[httpx.AsyncClient, None]:
    """Dependency to provide a shared HTTP client."""
    async with httpx.AsyncClient() as client:
        yield client


def get_cognito_client(
    settings: Annotated[Settings, Depends(get_app_settings)],
) -> Any:
    """Dependency to provide a Cognito Boto3 client."""
    return boto3.client(
        "cognito-idp",
        region_name=settings.cognito_region,
    )


async def get_token_verifier(
    settings: Annotated[Settings, Depends(get_app_settings)],
    logger: Annotated[BoundLogger, Depends(get_logger)],
    http_client: Annotated[httpx.AsyncClient, Depends(get_http_client)],
) -> TokenVerifier:
    """Dependency that provides a TokenVerifier interface."""
    return CognitoTokenVerifier(
        settings=settings,
        logger=logger,
        http_client=http_client,
    )


async def get_user_manager(
    settings: Annotated[Settings, Depends(get_app_settings)],
    logger: Annotated[BoundLogger, Depends(get_logger)],
    cognito_client: Annotated[Any, Depends(get_cognito_client)],
) -> UserManager:
    """Dependency that provides a UserManager interface."""
    return CognitoUserManager(
        settings=settings,
        logger=logger,
        cognito_client=cognito_client,
    )


async def get_authenticator(
    settings: Annotated[Settings, Depends(get_app_settings)],
    logger: Annotated[BoundLogger, Depends(get_logger)],
    cognito_client: Annotated[Any, Depends(get_cognito_client)],
) -> Authenticator:
    """Dependency that provides an Authenticator interface."""
    return CognitoAuthenticator(
        settings=settings,
        logger=logger,
        cognito_client=cognito_client,
    )


async def get_current_user(
    token: Annotated[HTTPAuthorizationCredentials, Depends(reusable_oauth2)],
    verifier: Annotated[TokenVerifier, Depends(get_token_verifier)],
) -> dict[str, Any]:
    """Dependency to retrieve the current user from a JWT."""
    return await verifier.verify_token(token.credentials)
