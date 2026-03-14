from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from structlog.stdlib import BoundLogger


class BaseService:
    """
    Base class for all business logic services.
    Provides standard access to the logger and database session.
    """

    def __init__(self, db: AsyncSession, logger: BoundLogger) -> None:
        self.db = db
        self.logger = logger

    @asynccontextmanager
    async def transaction(self) -> AsyncGenerator[None, None]:
        """
        Standard context manager for handling database transactions.
        Ensures that operations are committed if successful, or rolled back on error.
        """
        try:
            yield
            await self.db.commit()
        except Exception as e:
            await self.db.rollback()
            self.log_error("Transaction failed, rolling back", error=str(e))
            raise e

    def log_info(self, event: str, **kwargs: Any) -> None:
        """Helper to log informative events with service context."""
        self.logger.info(event, service=self.__class__.__name__, **kwargs)

    def log_error(self, event: str, **kwargs: Any) -> None:
        """Helper to log error events with service context."""
        self.logger.error(event, service=self.__class__.__name__, **kwargs)
