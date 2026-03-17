import uuid
from dataclasses import fields
from typing import Generic, TypeVar

from ..entities.base import Entity
from ..interfaces.crud_repository import ICrudRepository

E = TypeVar("E", bound=Entity)
CreateDTO = TypeVar("CreateDTO")
UpdateDTO = TypeVar("UpdateDTO")


class CrudUseCase(Generic[E, CreateDTO, UpdateDTO]):
    """
    Generic CRUD use case that eliminates per-entity boilerplate.

    Subclasses must implement:
      - _build_entity(data: CreateDTO) -> E
      - _apply_updates(entity: E, data: UpdateDTO) -> E

    For a custom save method name (e.g. `save_client`), override `_save`.
    """

    entity_name: str = "Entity"

    def __init__(self, repo: ICrudRepository[E]):
        self.repo = repo

    # --- Public API (stable for all entities) ---

    def create(self, data: CreateDTO) -> E:
        entity = self._build_entity(data)
        self._save(entity)
        return entity

    def get(self, entity_id: uuid.UUID) -> E | None:
        return self.repo.get_by_id(entity_id)

    def update(self, entity_id: uuid.UUID, data: UpdateDTO) -> E:
        entity = self.repo.get_by_id(entity_id)
        if not entity:
            raise ValueError(f"{self.entity_name} not found")
        entity = self._apply_updates(entity, data)
        self._save(entity)
        return entity

    def delete(self, entity_id: uuid.UUID) -> None:
        self.repo.delete(entity_id)

    def list(self, limit: int, offset: int) -> list[E]:
        return self.repo.list(limit=limit, offset=offset)

    # --- Hooks for subclasses ---

    def _build_entity(self, data: CreateDTO) -> E:
        raise NotImplementedError

    def _apply_updates(self, entity: E, data: UpdateDTO) -> E:
        """Default: set all non-None fields from the UpdateDTO onto the entity."""
        for f in fields(data):  # type: ignore[arg-type]
            value = getattr(data, f.name)
            if value is not None:
                setattr(entity, f.name, value)
        return entity

    def _save(self, entity: E) -> None:
        """Override if the repo method is not `save` (e.g. `save_client`)."""
        self.repo.save(entity)
