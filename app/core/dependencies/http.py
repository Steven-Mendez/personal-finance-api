from typing import cast

import httpx
from fastapi import Request


def get_http_client(request: Request) -> httpx.AsyncClient:
    """Dependency to provide the pre-warmed HTTP client from app state."""
    return cast(httpx.AsyncClient, request.app.state.http_client)
