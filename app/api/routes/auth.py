from typing import Annotated, Any

from fastapi import APIRouter, Depends, status

from app.api.dependencies import (
    get_authenticator,
    get_current_user,
    get_user_manager,
)
from app.schemas.user_create import UserCreate
from app.services.auth import Authenticator, UserManager

router = APIRouter()


@router.post("/auth/login")
async def login(
    user_in: UserCreate,
    authenticator: Annotated[Authenticator, Depends(get_authenticator)],
) -> dict[str, Any]:
    """Endpoint to authenticate a user and return tokens."""
    return await authenticator.login(user_in.email, user_in.password)


@router.get("/auth/me")
async def get_me(
    current_user: Annotated[dict[str, Any], Depends(get_current_user)],
) -> dict[str, Any]:
    """Endpoint to retrieve details of the currently authenticated user."""
    return {"user": current_user}


@router.post("/auth/users", status_code=status.HTTP_201_CREATED)
async def create_user(
    user_in: UserCreate,
    user_manager: Annotated[UserManager, Depends(get_user_manager)],
) -> dict[str, Any]:
    """Endpoint for administrators to create a new user account."""
    user = await user_manager.create_user(user_in.email, user_in.password)
    return {"user": user}


@router.get("/auth/users")
async def list_users(
    user_manager: Annotated[UserManager, Depends(get_user_manager)],
    current_user: Annotated[dict[str, Any], Depends(get_current_user)],
) -> dict[str, Any]:
    """Endpoint for administrators to list all available user accounts."""
    users = await user_manager.list_users()
    return {"users": users}
