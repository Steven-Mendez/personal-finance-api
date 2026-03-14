from typing import Annotated, Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.services.auth.base import Authenticator, TokenVerifier, UserManager
from app.services.cognito.cognito import CognitoAuthService

reusable_oauth2 = HTTPBearer()


async def get_auth_service() -> CognitoAuthService:
    """Provide a concrete implementation of auth services."""
    return CognitoAuthService()


async def get_token_verifier(
    service: Annotated[CognitoAuthService, Depends(get_auth_service)],
) -> TokenVerifier:
    """Dependency that provides a TokenVerifier interface."""
    return service


async def get_user_manager(
    service: Annotated[CognitoAuthService, Depends(get_auth_service)],
) -> UserManager:
    """Dependency that provides a UserManager interface."""
    return service


async def get_authenticator(
    service: Annotated[CognitoAuthService, Depends(get_auth_service)],
) -> Authenticator:
    """Dependency that provides an Authenticator interface."""
    return service


async def get_current_user(
    token: Annotated[HTTPAuthorizationCredentials, Depends(reusable_oauth2)],
    verifier: Annotated[TokenVerifier, Depends(get_token_verifier)],
) -> dict[str, Any]:
    """Dependency to retrieve the current user from a JWT."""
    try:
        user = await verifier.verify_token(token.credentials)
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        ) from e
