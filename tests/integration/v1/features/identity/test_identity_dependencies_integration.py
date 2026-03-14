from unittest.mock import AsyncMock

import pytest

from app.api.v1.features.identity.dependencies import get_current_user
from app.api.v1.features.identity.exceptions import InvalidTokenError


@pytest.mark.asyncio
async def test_get_current_user_success() -> None:
    token = "valid_token"
    mock_auth_service = AsyncMock()
    mock_claims = {
        "sub": "user_id",
        "iss": "iss",
        "aud": "aud",
        "exp": 1,
        "iat": 1,
    }
    mock_auth_service.verify_token.return_value = mock_claims

    user = await get_current_user(token, mock_auth_service)

    assert user == mock_claims
    mock_auth_service.verify_token.assert_awaited_once_with("valid_token")


@pytest.mark.asyncio
async def test_get_current_user_invalid_token() -> None:
    token = "invalid_token"
    mock_auth_service = AsyncMock()
    mock_auth_service.verify_token.side_effect = InvalidTokenError("Invalid token")

    with pytest.raises(InvalidTokenError) as exc_info:
        await get_current_user(token, mock_auth_service)

    assert str(exc_info.value) == "Invalid token"
