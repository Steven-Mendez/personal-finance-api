import os

import pytest


@pytest.fixture(scope="session")
def base_url() -> str:
    url = os.getenv("E2E_BASE_URL")
    if not url:
        pytest.skip("Set E2E_BASE_URL to run e2e tests")
    return url.rstrip("/")
