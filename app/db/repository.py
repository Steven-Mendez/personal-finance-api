from collections.abc import Sequence
from typing import Any, Generic, TypeVar
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies.pagination import PaginationParams
from app.db.base import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    """
    Generic repository providing base CRUD operations.
    Follows Vertical Slice Architecture by being a mixin/base for specific slices.
    """

    def __init__(self, model: type[ModelT], session: AsyncSession) -> None:
        self.model = model
        self.session = session

    async def get_by_id(self, id: UUID) -> ModelT | None:
        """Fetch a single record by its UUID."""
        query = select(self.model).where(self.model.id == id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def list_all(self, limit: int = 100, offset: int = 0) -> Sequence[ModelT]:
        """Fetch a list of records with pagination."""
        query = select(self.model).offset(offset).limit(limit)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def count(self) -> int:
        """Count the total number of records."""
        query = select(func.count()).select_from(self.model)
        result = await self.session.execute(query)
        return int(result.scalar_one())

    async def get_paginated(
        self, params: PaginationParams
    ) -> tuple[Sequence[ModelT], int]:
        """
        Fetch a paginated list of records and the total count.
        Returns a tuple of (items, total_count).
        """
        total = await self.count()
        items = await self.list_all(limit=params.limit, offset=params.offset)
        return items, total

    async def create(self, **data: Any) -> ModelT:
        """Create a new record in the database."""
        instance = self.model(**data)
        self.session.add(instance)
        await self.session.flush()
        return instance

    async def update(self, id: UUID, **data: Any) -> ModelT | None:
        """Update an existing record in the database."""
        instance = await self.get_by_id(id)
        if not instance:
            return None

        for key, value in data.items():
            if hasattr(instance, key):
                setattr(instance, key, value)

        await self.session.flush()
        return instance

    async def delete(self, id: UUID) -> bool:
        """Delete a record from the database."""
        instance = await self.get_by_id(id)
        if instance:
            await self.session.delete(instance)
            await self.session.flush()
            return True
        return False
