import uuid
from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from ..entities.base import Entity

T = TypeVar("T", bound=Entity)


class ICrudRepository(ABC, Generic[T]):
    """Generic repository interface providing standard CRUD operations."""

    @abstractmethod
    def get_by_id(self, entity_id: uuid.UUID) -> T | None:
        pass

    @abstractmethod
    def save(self, entity: T) -> None:
        pass

    @abstractmethod
    def delete(self, entity_id: uuid.UUID) -> None:
        pass

    @abstractmethod
    def list(self, limit: int, offset: int) -> list[T]:
        pass
