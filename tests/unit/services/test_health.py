import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from app.services.health import build_liveness_payload, build_readiness_payload, check_dependencies


def test_build_liveness_payload_returns_alive_status() -> None:
    # Given / When
    payload = build_liveness_payload()

    # Then
    assert payload == {"status": "alive"}


@pytest.mark.parametrize(
    "dependencies,expected_status",
    [
        ({}, "ready"),
        ({"api": "healthy"}, "ready"),
        ({"api": "healthy", "db": "healthy"}, "ready"),
        ({"api": "unhealthy"}, "unready"),
        ({"api": "healthy", "db": "unhealthy"}, "unready"),
        ({"api": "unhealthy", "db": "unhealthy"}, "unready"),
    ],
)
def test_build_readiness_payload_derives_status_from_dependencies(
    dependencies: dict[str, str], expected_status: str
) -> None:
    # Given / When
    payload = build_readiness_payload(dependencies)

    # Then
    assert payload["status"] == expected_status
    assert payload["dependencies"] == dependencies


def test_check_dependencies_returns_healthy_by_default() -> None:
    # Given: check_api is a stub that always returns True

    # When
    result = asyncio.run(check_dependencies())

    # Then
    assert result == {"api": "healthy"}


def test_check_dependencies_returns_unhealthy_when_check_api_raises() -> None:
    # Given: the underlying check raises an unexpected error
    async def failing_check_api() -> bool:
        raise RuntimeError("connection refused")

    with patch("app.services.health.check_api", failing_check_api):
        # When
        result = asyncio.run(check_dependencies())

    # Then
    assert result == {"api": "unhealthy"}


def test_check_dependencies_returns_unhealthy_when_check_api_returns_false() -> None:
    # Given: the underlying check reports a degraded state
    async def degraded_check_api() -> bool:
        return False

    with patch("app.services.health.check_api", degraded_check_api):
        # When
        result = asyncio.run(check_dependencies())

    # Then
    assert result == {"api": "unhealthy"}


def test_check_dependencies_returns_unhealthy_on_timeout() -> None:
    # Given: the health checks exceed the timeout budget — patch wait_for so
    # the test is instant rather than waiting the full 2-second deadline
    with patch("asyncio.wait_for", new=AsyncMock(side_effect=asyncio.TimeoutError)):
        # When
        result = asyncio.run(check_dependencies())

    # Then
    assert result == {"api": "unhealthy"}
