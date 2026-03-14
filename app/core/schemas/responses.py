from datetime import datetime, timezone
from typing import Generic, Literal, TypeVar

from pydantic import BaseModel, Field

DataT = TypeVar("DataT")


class ResponseMetadata(BaseModel):
    """Metadata for all API responses."""

    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    version: str = "v1"


class ResponseEnvelope(BaseModel, Generic[DataT]):
    """Standardized API response envelope."""

    status: Literal["success", "error"] = "success"
    data: DataT
    metadata: ResponseMetadata = Field(default_factory=ResponseMetadata)
