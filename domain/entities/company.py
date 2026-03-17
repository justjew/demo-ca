from dataclasses import dataclass, field

from .base import Entity


@dataclass(kw_only=True)
class LoyaltyLevel(Entity):
    name: str
    min_spent_amount: int
    accrual_rate: float


@dataclass(kw_only=True)
class Company(Entity):
    name: str
    tax_id: str
    # If empty, a default fallback rate is used.
    loyalty_levels: list[LoyaltyLevel] = field(default_factory=list)
    max_loyalty_payment_percent: float = 0.50

    def get_loyalty_accrual_rate_for_spent(self, total_spent: int) -> float:
        if not self.loyalty_levels:
            return 0.05  # Default fallback

        # Sort levels by min_spent_amount descending
        sorted_levels = sorted(self.loyalty_levels, key=lambda lvl: lvl.min_spent_amount, reverse=True)
        for level in sorted_levels:
            if total_spent >= level.min_spent_amount:
                return level.accrual_rate
        
        # If below all levels, return the lowest level's rate or a default
        # Assuming we want to return the minimum configured rate if they haven't reached any level
        return 0.05
