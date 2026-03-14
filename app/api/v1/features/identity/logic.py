from abc import ABC, abstractmethod
from typing import Any


class Authenticator(ABC):
    @abstractmethod
    async def login(self, email: str, password: str) -> dict[str, Any]:
        """Authenticate a user and return tokens."""
        pass


class TokenVerifier(ABC):
    @abstractmethod
    async def verify_token(self, token: str) -> dict[str, Any]:
        """Verify a JWT token and return its claims."""
        pass


class UserManager(ABC):
    @abstractmethod
    async def create_user(self, email: str, password: str) -> dict[str, Any]:
        """Create a new user in the identity provider."""
        pass

    @abstractmethod
    async def list_users(self) -> list[dict[str, Any]]:
        """List users from the identity provider."""
        pass
