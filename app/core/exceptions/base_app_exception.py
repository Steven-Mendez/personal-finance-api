from typing import Any


class BaseAppException(Exception):
    """
    Base exception for all application-specific errors.
    Features should inherit from this class to provide consistent error reporting.
    """

    def __init__(
        self,
        message: str,
        status_code: int = 400,
        error_code: str | None = None,
        data: dict[str, Any] | None = None,
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.data = data
        super().__init__(self.message)


class NotFoundError(BaseAppException):
    """Exception raised when a requested resource is not found."""

    def __init__(
        self, message: str = "Resource not found", data: dict[str, Any] | None = None
    ):
        super().__init__(
            message=message,
            status_code=404,
            error_code="NOT_FOUND",
            data=data,
        )
