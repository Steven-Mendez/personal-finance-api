from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.config import Settings
from app.features.health.logic import (
    ApiHealthCheck,
    CognitoHealthCheck,
    DefaultHealthService,
)


@pytest.fixture
def settings() -> Settings:
    return Settings()


@pytest.fixture
def logger() -> MagicMock:
    return MagicMock()


@pytest.fixture
def http_client() -> AsyncMock:
    return AsyncMock()


class TestApiHealthCheck:
    @pytest.mark.asyncio
    async def test_check_returns_healthy(self) -> None:
        check = ApiHealthCheck()
        name, status = await check.check()
        assert name == "api"
        assert status == "healthy"


class TestCognitoHealthCheck:
    @pytest.mark.asyncio
    async def test_check_cognito_healthy(
        self, settings: Settings, logger: MagicMock, http_client: AsyncMock
    ) -> None:
        mock_response = MagicMock()
        mock_response.status_code = 200
        http_client.get.return_value = mock_response

        check = CognitoHealthCheck(settings, logger, http_client)
        name, status = await check.check()

        assert name == "cognito"
        assert status == "healthy"

    @pytest.mark.asyncio
    async def test_check_cognito_unhealthy(
        self, settings: Settings, logger: MagicMock, http_client: AsyncMock
    ) -> None:
        mock_response = MagicMock()
        mock_response.status_code = 404
        http_client.get.return_value = mock_response

        check = CognitoHealthCheck(settings, logger, http_client)
        name, status = await check.check()

        assert name == "cognito"
        assert status == "unhealthy"

    @pytest.mark.asyncio
    async def test_check_cognito_exception(
        self, settings: Settings, logger: MagicMock, http_client: AsyncMock
    ) -> None:
        http_client.get.side_effect = Exception("network error")

        check = CognitoHealthCheck(settings, logger, http_client)
        name, status = await check.check()

        assert name == "cognito"
        assert status == "unhealthy"
        logger.error.assert_called_once()


class TestDefaultHealthService:
    def test_build_liveness_payload_returns_alive_status(self) -> None:
        service = DefaultHealthService(checks=[])
        payload = service.build_liveness_payload()
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
        self,
        dependencies: dict[str, str],
        expected_status: str,
    ) -> None:
        service = DefaultHealthService(checks=[])
        payload = service.build_readiness_payload(dependencies)
        assert payload.status == expected_status
        assert payload.dependencies == dependencies

    @pytest.mark.asyncio
    async def test_check_dependencies_aggregates_results(self) -> None:
        mock_check_1 = AsyncMock()
        mock_check_1.check.return_value = ("api", "healthy")
        mock_check_2 = AsyncMock()
        mock_check_2.check.return_value = ("cognito", "unhealthy")

        service = DefaultHealthService(checks=[mock_check_1, mock_check_2])
        result = await service.check_dependencies()

        assert result == {"api": "healthy", "cognito": "unhealthy"}
        mock_check_1.check.assert_called_once()
        mock_check_2.check.assert_called_once()
