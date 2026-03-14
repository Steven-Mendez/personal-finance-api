from abc import ABC, abstractmethod
from typing import Any


class UserManager(ABC):
    @abstractmethod
    async def create_user(self, email: str, password: str) -> dict[str, Any]:
        """Create a new user in the identity provider."""
        pass

    @abstractmethod
    async def list_users(self) -> list[dict[str, Any]]:
        """List users from the identity provider."""
        pass
