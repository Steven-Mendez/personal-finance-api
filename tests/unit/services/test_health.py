import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from app.services.health import (
    build_liveness_payload,
    build_readiness_payload,
    check_cognito,
    check_dependencies,
)


def test_build_liveness_payload_returns_alive_status() -> None:
    # Given / When
    payload = build_liveness_payload()

    # Then
    assert payload.status == "alive"


@pytest.mark.parametrize(
    "dependencies,expected_status",
    [
        ({}, "ready"),
        ({"api": "healthy"}, "ready"),
        ({"api": "healthy", "cognito": "healthy"}, "ready"),
        ({"api": "unhealthy"}, "unready"),
        ({"api": "healthy", "cognito": "unhealthy"}, "unready"),
        ({"api": "unhealthy", "cognito": "unhealthy"}, "unready"),
    ],
)
def test_build_readiness_payload_derives_status_from_dependencies(
    dependencies: dict[str, str], expected_status: str
) -> None:
    # Given / When
    payload = build_readiness_payload(dependencies)

    # Then
    assert payload.status == expected_status
    assert payload.dependencies == dependencies


@pytest.mark.asyncio
async def test_check_cognito_healthy() -> None:
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        from unittest.mock import MagicMock

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        assert await check_cognito() is True


@pytest.mark.asyncio
async def test_check_cognito_unhealthy() -> None:
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        from unittest.mock import MagicMock

        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        assert await check_cognito() is False


@pytest.mark.asyncio
async def test_check_dependencies_returns_healthy_by_default() -> None:
    with (
        patch("app.services.health.check_api", return_value=True),
        patch("app.services.health.check_cognito", return_value=True),
    ):
        result = await check_dependencies()

        assert result == {"api": "healthy", "cognito": "healthy"}


@pytest.mark.asyncio
async def test_check_dependencies_returns_unhealthy_when_check_api_raises() -> None:
    with (
        patch("app.services.health.check_api", side_effect=Exception("boom")),
        patch("app.services.health.check_cognito", return_value=True),
    ):
        result = await check_dependencies()

        assert result == {"api": "unhealthy", "cognito": "healthy"}


@pytest.mark.asyncio
async def test_check_dependencies_returns_unhealthy_on_timeout() -> None:
    with patch("asyncio.wait_for", side_effect=asyncio.TimeoutError):
        result = await check_dependencies()

    assert result == {"api": "unhealthy", "cognito": "unhealthy"}
