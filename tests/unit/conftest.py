from collections.abc import Generator

import pytest
from pytest_socket import disable_socket, enable_socket


@pytest.fixture(autouse=True)
def block_network() -> Generator[None, None, None]:
    # Unit tests are pure Python and must never reach the network.
    # allow_unix_socket=True permits the AF_UNIX socketpair that asyncio's
    # event loop uses internally, while still blocking TCP/UDP network calls.
    # If a test triggers a real network socket it will fail here — move it
    # to integration/ or e2e/ instead.
    disable_socket(allow_unix_socket=True)
    yield
    enable_socket()
