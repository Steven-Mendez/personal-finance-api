from app.core.exceptions.base_app_exception import BaseAppException


class InvalidTokenError(BaseAppException):
    """Raised when a provided token is invalid, expired, or tampered with."""

    pass
