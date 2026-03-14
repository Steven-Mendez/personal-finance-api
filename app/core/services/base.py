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

    def log_info(self, event: str, **kwargs: Any) -> None:
        """Helper to log informative events with service context."""
        self.logger.info(event, service=self.__class__.__name__, **kwargs)

    def log_error(self, event: str, **kwargs: Any) -> None:
        """Helper to log error events with service context."""
        self.logger.error(event, service=self.__class__.__name__, **kwargs)
