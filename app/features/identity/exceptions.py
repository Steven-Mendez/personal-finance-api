from app.core.exceptions.base_app_exception import BaseAppException


class AuthenticationError(BaseAppException):
    """Raised when authentication fails (e.g., invalid credentials)."""

    pass


class InvalidTokenError(BaseAppException):
    """Raised when a provided token is invalid, expired, or tampered with."""

    pass


class UserManagementError(BaseAppException):
    """Raised when a user management operation fails."""

    pass
