from typing import Any

from fastapi import Request


def get_cognito_client(request: Request) -> Any:
    """Provides the pre-warmed Cognito client from the app state."""
    return request.app.state.cognito_client
