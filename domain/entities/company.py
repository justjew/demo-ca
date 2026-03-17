from dataclasses import dataclass
from typing import List
from .base import Entity

@dataclass(kw_only=True)
class Company(Entity):
    name: str
    tax_id: str
    # In a real app, might hold configuration for global loyalty rules, etc.
    loyalty_accrual_rate: float = 0.05
    max_loyalty_payment_percent: float = 0.50

    def get_loyalty_accrual_rate(self) -> float:
        return self.loyalty_accrual_rate
