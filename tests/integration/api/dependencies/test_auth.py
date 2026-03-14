from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials

from app.api.dependencies.auth import get_current_user


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
    mock_auth_service.verify_token.side_effect = ValueError("Invalid token")

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(token, mock_auth_service)

    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert exc_info.value.detail == "Invalid token"
