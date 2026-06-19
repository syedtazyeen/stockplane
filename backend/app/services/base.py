from typing import Generic, TypeVar
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.base import BaseRepository


R = TypeVar("R", bound=BaseRepository)


class BaseService(Generic[R]):
    """Base service."""

    def __init__(
        self,
        repository: R,
    ) -> None:
        self.repository = repository

    @property
    def db(self) -> AsyncSession:
        return self.repository.db
