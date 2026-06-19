from typing import Any, Generic, TypeVar
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import Base

M = TypeVar("M", bound=Base)


class BaseRepository(Generic[M]):
    """Base repository for all repositories"""

    model: type[M]

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, *, id: Any):  # pylint: disable=redefined-builtin
        result = await self.db.execute(select(self.model).where(self.model.id == id))
        return result.scalar_one_or_none()

    async def create(self, *, obj: M):
        self.db.add(obj)
        await self.db.flush()
        return obj

    async def delete(self, *, obj: M):
        await self.db.delete(obj)
