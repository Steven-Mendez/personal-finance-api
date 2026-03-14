from abc import ABC, abstractmethod
from typing import Any

from .schemas import TokenResponse, UserResponse


class Authenticator(ABC):
    @abstractmethod
    async def login(self, email: str, password: str) -> TokenResponse:
        pass


class TokenVerifier(ABC):
    @abstractmethod
    async def verify_token(self, token: str) -> dict[str, Any]:
        # Claims vary too much to have a single static model,
        # but we can improve this later if needed.
        pass


class UserManager(ABC):
    @abstractmethod
    async def create_user(self, email: str, password: str) -> UserResponse:
        pass

    @abstractmethod
    async def list_users(self) -> list[UserResponse]:
        pass
