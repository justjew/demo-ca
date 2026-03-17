import uuid
from dataclasses import dataclass

from ..exceptions import InsufficientPointsError
from .base import Entity


@dataclass(kw_only=True)
class LoyaltyProfile(Entity):
    client_id: uuid.UUID
    company_id: uuid.UUID
    balance: int = 0
    total_spent: int = 0  # In minor units (cents)

    # We could have levels (Bronze, Silver, Gold) depending on total spent.
    # For now, base implementation.

    def can_spend(self, points: int) -> bool:
        return self.balance >= points

    def spend_points(self, points: int) -> None:
        if not self.can_spend(points):
            raise InsufficientPointsError(f"Cannot spend {points} points. Balance is {self.balance}.")
        self.balance -= points

    def add_points(self, points: int) -> None:
        if points < 0:
            raise ValueError("Cannot add negative points.")
        self.balance += points

@dataclass(kw_only=True)
class Client(Entity):
    phone_number: str
    first_name: str | None = None
    last_name: str | None = None
