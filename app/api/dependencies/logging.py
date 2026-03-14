from typing import cast

import structlog
from structlog.stdlib import BoundLogger


def get_logger() -> BoundLogger:
    """Dependency providing a context-aware structlog logger."""
    return cast(BoundLogger, structlog.get_logger())
