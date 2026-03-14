from collections.abc import AsyncGenerator

import httpx


async def get_http_client() -> AsyncGenerator[httpx.AsyncClient, None]:
    """Dependency to provide a shared HTTP client."""
    async with httpx.AsyncClient() as client:
        yield client
