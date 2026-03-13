import json
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

import pytest


@pytest.mark.e2e
def test_readiness_endpoint_is_healthy(base_url: str) -> None:
    try:
        with urlopen(f"{base_url}/health/ready", timeout=5) as response:
            assert response.status == 200
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        pytest.fail(f"Readiness endpoint returned HTTP {exc.code}")
    except URLError as exc:
        pytest.fail(f"Readiness endpoint unreachable: {exc.reason}")

    assert payload == {"status": "ready", "dependencies": {"api": "healthy"}}
