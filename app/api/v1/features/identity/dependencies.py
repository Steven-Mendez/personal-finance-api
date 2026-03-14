from typing import Annotated, Any

import httpx
from fastapi import Depends
from fastapi.security import OAuth2AuthorizationCodeBearer
from structlog.stdlib import BoundLogger

from app.core.config import Settings, get_settings
from app.core.dependencies.cognito import get_cognito_client
from app.core.dependencies.http import get_http_client
from app.core.dependencies.logging import get_logger
from app.core.dependencies.settings import get_app_settings

from .logic import Authenticator, TokenVerifier, UserManager
from .providers.cognito.cognito_authenticator import CognitoAuthenticator
from .providers.cognito.cognito_token_verifier import CognitoTokenVerifier
from .providers.cognito.cognito_user_manager import CognitoUserManager
from .schemas import BaseJWTPayload

# Initialize settings to build OAuth2 scheme
_settings = get_settings()

reusable_oauth2 = OAuth2AuthorizationCodeBearer(
    authorizationUrl=_settings.cognito_oauth_authorize_url,
    tokenUrl=_settings.cognito_oauth_token_url,
    scopes={
        "openid": "OpenID Connect",
        "email": "Read email address",
        "profile": "Read user profile",
    },
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
    token: Annotated[str, Depends(reusable_oauth2)],
    verifier: Annotated[TokenVerifier, Depends(get_token_verifier)],
) -> BaseJWTPayload:
    """Dependency to retrieve the current user from a JWT."""
    return await verifier.verify_token(token)
