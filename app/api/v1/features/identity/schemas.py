from typing import Any

from pydantic import BaseModel, EmailStr, SecretStr


class UserCreate(BaseModel):
    """Schema for user creation requests."""

    email: EmailStr
    password: SecretStr


class TokenResponse(BaseModel):
    """Schema for authentication token responses."""

    AccessToken: str
    IdToken: str
    RefreshToken: str
    ExpiresIn: int
    TokenType: str


class UserResponse(BaseModel):
    """Schema for user details."""

    Username: str
    Attributes: list[dict[str, Any]] | None = None
    UserCreateDate: Any | None = None
    UserLastModifiedDate: Any | None = None
    Enabled: bool | None = None
    UserStatus: str | None = None


class UserListResponse(BaseModel):
    """Schema for a list of users."""

    users: list[UserResponse]
