from abc import ABC, abstractmethod
from typing import Any


class TokenVerifier(ABC):
    @abstractmethod
    async def verify_token(self, token: str) -> dict[str, Any]:
        """Verify a JWT token and return its claims."""
        pass
