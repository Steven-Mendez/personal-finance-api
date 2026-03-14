from app.core.exceptions.base_app_exception import BaseAppException


class AuthenticationError(BaseAppException):
    """Raised when authentication fails (e.g., invalid credentials)."""

    pass
