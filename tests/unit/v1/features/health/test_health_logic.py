from unittest.mock import AsyncMock, MagicMock

import pytest

from app.api.v1.features.health.logic import (
    ApiHealthCheck,
    CognitoHealthCheck,
    DefaultHealthService,
)
from app.api.v1.features.health.schemas import HealthStatus, ReadinessResponse


class TestApiHealthCheck:
    @pytest.mark.asyncio
    async def test_check_returns_healthy(self) -> None:
        mock_http = MagicMock()
        check = ApiHealthCheck(mock_http)
        name, status = await check.check()
        assert name == "api"
        assert status == "healthy"


class TestCognitoHealthCheck:
    @pytest.mark.asyncio
    async def test_check_cognito_healthy(self) -> None:
        mock_cognito = MagicMock()
        mock_cognito.describe_user_pool.return_value = {}
        check = CognitoHealthCheck(mock_cognito, "user-pool-id")
        name, status = await check.check()
        assert name == "cognito"
        assert status == "healthy"

    @pytest.mark.asyncio
    async def test_check_cognito_unhealthy(self) -> None:
        mock_cognito = MagicMock()
        mock_cognito.describe_user_pool.side_effect = Exception("Cognito is down")
        check = CognitoHealthCheck(mock_cognito, "user-pool-id")
        name, status = await check.check()
        assert name == "cognito"
        assert status == "unhealthy"

    @pytest.mark.asyncio
    async def test_check_cognito_exception(self) -> None:
        mock_cognito = MagicMock()
        mock_cognito.describe_user_pool.side_effect = Exception("Connection error")
        check = CognitoHealthCheck(mock_cognito, "user-pool-id")
        name, status = await check.check()
        assert name == "cognito"
        assert status == "unhealthy"


class TestDefaultHealthService:
    @pytest.fixture
    def mock_api_check(self) -> MagicMock:
        check = MagicMock(spec=ApiHealthCheck)
        check.check = AsyncMock(return_value=("api", "healthy"))
        return check

    @pytest.fixture
    def mock_cognito_check(self) -> MagicMock:
        check = MagicMock(spec=CognitoHealthCheck)
        check.check = AsyncMock(return_value=("cognito", "healthy"))
        return check

    @pytest.fixture
    def health_service(
        self, mock_api_check: MagicMock, mock_cognito_check: MagicMock
    ) -> DefaultHealthService:
        return DefaultHealthService(
            api_check=mock_api_check,
            cognito_check=mock_cognito_check,
            logger=MagicMock(),
        )

    def test_build_liveness_payload_returns_alive_status(
        self, health_service: DefaultHealthService
    ) -> None:
        payload = health_service.build_liveness_payload()
        assert isinstance(payload, HealthStatus)
        assert payload.status == "alive"

    @pytest.mark.parametrize(
        "dependencies, expected_status",
        [
            ({"api": "healthy", "cognito": "healthy"}, "ready"),
            ({"api": "unhealthy", "cognito": "healthy"}, "unready"),
            ({"api": "healthy", "cognito": "unhealthy"}, "unready"),
            ({"api": "unhealthy", "cognito": "unhealthy"}, "unready"),
        ],
    )
    def test_build_readiness_payload_derives_status_from_dependencies(
        self,
        health_service: DefaultHealthService,
        dependencies: dict,
        expected_status: str,
    ) -> None:
        payload = health_service.build_readiness_payload(dependencies)
        assert isinstance(payload, ReadinessResponse)
        assert payload.status == expected_status
        assert payload.dependencies == dependencies

    @pytest.mark.asyncio
    async def test_check_dependencies_aggregates_results(
        self, health_service: DefaultHealthService
    ) -> None:
        results = await health_service.check_dependencies()
        assert results == {"api": "healthy", "cognito": "healthy"}
