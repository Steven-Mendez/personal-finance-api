from datetime import datetime, timezone
from typing import Any, Generic, Literal, TypeVar

from asgi_correlation_id.context import correlation_id
from pydantic import BaseModel, Field

DataT = TypeVar("DataT")


class ResponseMetadata(BaseModel):
    """Metadata for all API responses."""

    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    version: str = "v1"
    request_id: str | None = Field(default_factory=lambda: correlation_id.get())


class ErrorDetail(BaseModel):
    """Detailed error information."""

    message: str
    error_code: str | None = None
    data: dict[str, Any] | None = None


class ResponseEnvelope(BaseModel, Generic[DataT]):
    """Standardized API response envelope."""

    status: Literal["success", "error"] = "success"
    data: DataT | None = None
    error: ErrorDetail | None = None
    metadata: ResponseMetadata = Field(default_factory=ResponseMetadata)


class PaginationMetadata(BaseModel):
    """Metadata specific to paginated responses."""

    total_items: int
    limit: int
    offset: int


class PaginatedResponseEnvelope(BaseModel, Generic[DataT]):
    """Standardized API response envelope for lists of items."""

    status: Literal["success", "error"] = "success"
    data: list[DataT]
    pagination: PaginationMetadata
    metadata: ResponseMetadata = Field(default_factory=ResponseMetadata)
