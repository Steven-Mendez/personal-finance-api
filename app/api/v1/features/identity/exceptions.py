from typing import Any

from app.core.exceptions.base_app_exception import BaseAppException


class AuthenticationError(BaseAppException):
    """Exception raised for authentication-related failures."""

    def __init__(
        self, message: str = "Authentication failed", data: dict[str, Any] | None = None
    ):
        super().__init__(
            message=message,
            status_code=401,
            error_code="AUTH_ERROR",
            data=data,
        )


class InvalidTokenError(BaseAppException):
    """Exception raised when an authentication token is invalid or expired."""

    def __init__(
        self,
        message: str = "Invalid or expired token",
        data: dict[str, Any] | None = None,
    ):
        super().__init__(
            message=message,
            status_code=401,
            error_code="INVALID_TOKEN",
            data=data,
        )


class UserManagementError(BaseAppException):
    """Exception raised for user management-related failures (e.g., creation)."""

    def __init__(
        self,
        message: str = "User management operation failed",
        data: dict[str, Any] | None = None,
    ):
        super().__init__(
            message=message,
            status_code=400,
            error_code="USER_MGMT_ERROR",
            data=data,
        )
