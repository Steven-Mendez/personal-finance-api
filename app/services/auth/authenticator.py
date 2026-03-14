from abc import ABC, abstractmethod
from typing import Any


class Authenticator(ABC):
    @abstractmethod
    async def login(self, email: str, password: str) -> dict[str, Any]:
        """Authenticate a user and return tokens."""
        pass
