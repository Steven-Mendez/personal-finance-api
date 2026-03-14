from typing import Annotated

from fastapi import Query
from pydantic import BaseModel


class PaginationParams(BaseModel):
    limit: int
    offset: int


def get_pagination_params(
    limit: Annotated[int, Query(ge=1, le=100, description="Items per page")] = 20,
    offset: Annotated[int, Query(ge=0, description="Page offset")] = 0,
) -> PaginationParams:
    """Dependency to standardize pagination parameters across the API."""
    return PaginationParams(limit=limit, offset=offset)
