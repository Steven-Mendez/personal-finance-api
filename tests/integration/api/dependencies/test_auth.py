from unittest.mock import AsyncMock

import pytest
from fastapi.security import HTTPAuthorizationCredentials

from app.api.v1.features.identity.dependencies import get_current_user
from app.api.v1.features.identity.exceptions import InvalidTokenError


@pytest.mark.asyncio
async def test_get_current_user_success() -> None:
    token = HTTPAuthorizationCredentials(scheme="Bearer", credentials="valid_token")
    mock_auth_service = AsyncMock()
    mock_auth_service.verify_token.return_value = {"sub": "user_id"}

    user = await get_current_user(token, mock_auth_service)

    assert user == {"sub": "user_id"}
    mock_auth_service.verify_token.assert_awaited_once_with("valid_token")


@pytest.mark.asyncio
async def test_get_current_user_invalid_token() -> None:
    token = HTTPAuthorizationCredentials(scheme="Bearer", credentials="invalid_token")
    mock_auth_service = AsyncMock()
    mock_auth_service.verify_token.side_effect = InvalidTokenError("Invalid token")

    with pytest.raises(InvalidTokenError) as exc_info:
        await get_current_user(token, mock_auth_service)

    assert str(exc_info.value) == "Invalid token"
