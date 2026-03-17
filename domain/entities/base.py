import uuid
from dataclasses import dataclass, field
from typing import Any

@dataclass(kw_only=True)
class Entity:
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    
    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, type(self)):
            return False
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)
