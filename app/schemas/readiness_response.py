from typing import Literal

from pydantic import BaseModel

StatusLiteral = Literal["healthy", "unhealthy"]


class ReadinessResponse(BaseModel):
    status: Literal["ready", "unready"]
    dependencies: dict[str, StatusLiteral]
