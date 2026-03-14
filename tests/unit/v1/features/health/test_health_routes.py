import pytest

from app.api.v1.features.health.routes import read_root


@pytest.mark.asyncio
async def test_read_root_returns_version_values() -> None:
    # Given / When
    response = await read_root()

    # Then
    assert response.data == {"message": "Personal Finance API", "version": "v1"}
