from typing import Annotated, Any

from fastapi import APIRouter, Depends, status

from app.core.schemas.responses import ResponseEnvelope

from .dependencies import (
    get_authenticator,
    get_current_user,
    get_user_manager,
)
from .logic import Authenticator, UserManager
from .schemas import TokenResponse, UserCreate, UserListResponse, UserResponse

router = APIRouter()


@router.post("/login", response_model=ResponseEnvelope[TokenResponse])
async def login(
    user_in: UserCreate,
    authenticator: Annotated[Authenticator, Depends(get_authenticator)],
) -> ResponseEnvelope[TokenResponse]:
    """Endpoint to authenticate a user and return tokens."""
    token_data = await authenticator.login(
        user_in.email, user_in.password.get_secret_value()
    )
    return ResponseEnvelope(data=token_data)


@router.get("/me", response_model=ResponseEnvelope[dict[str, Any]])
async def get_me(
    current_user: Annotated[dict[str, Any], Depends(get_current_user)],
) -> ResponseEnvelope[dict[str, Any]]:
    """Endpoint to retrieve details of the currently authenticated user."""
    return ResponseEnvelope(data=current_user)


@router.post(
    "/users",
    status_code=status.HTTP_201_CREATED,
    response_model=ResponseEnvelope[UserResponse],
)
async def create_user(
    user_in: UserCreate,
    user_manager: Annotated[UserManager, Depends(get_user_manager)],
) -> ResponseEnvelope[UserResponse]:
    """Endpoint for administrators to create a new user account."""
    user = await user_manager.create_user(
        user_in.email, user_in.password.get_secret_value()
    )
    return ResponseEnvelope(data=user)


@router.get("/users", response_model=ResponseEnvelope[UserListResponse])
async def list_users(
    user_manager: Annotated[UserManager, Depends(get_user_manager)],
    current_user: Annotated[dict[str, Any], Depends(get_current_user)],
) -> ResponseEnvelope[UserListResponse]:
    """Endpoint for administrators to list all available user accounts."""
    users = await user_manager.list_users()
    return ResponseEnvelope(data=UserListResponse(users=users))
