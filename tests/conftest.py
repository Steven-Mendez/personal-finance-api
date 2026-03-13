import sys
from collections.abc import Generator
from pathlib import Path

import pytest

# Ensure the project root is on sys.path before importing app modules.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.config import get_settings  # noqa: E402


@pytest.fixture(autouse=True)
def reset_settings_cache() -> Generator[None, None, None]:
    # get_settings uses @lru_cache; clear it before and after every test so
    # that monkeypatched environment variables never leak across test boundaries.
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()
