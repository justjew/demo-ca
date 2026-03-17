import uuid
from dataclasses import dataclass, field

from ..value_objects import Money
from .base import Entity


@dataclass(kw_only=True)
class ModifierOption(Entity):
    name: str
    price_adjustment: Money
    is_available: bool = True

@dataclass(kw_only=True)
class ModifierGroup(Entity):
    name: str
    options: list[ModifierOption] = field(default_factory=list)
    is_required: bool = False
    min_selections: int = 0
    max_selections: int = 1

    def validate_selection(self, selected_option_ids: list[uuid.UUID]) -> bool:
        count = len(selected_option_ids)
        if count < self.min_selections:
            return False
        if count > self.max_selections:
            return False

        valid_ids = {opt.id for opt in self.options if opt.is_available}
        for opt_id in selected_option_ids:
            if opt_id not in valid_ids:
                return False
        return True

@dataclass(kw_only=True)
class Category(Entity):
    name: str
    is_active: bool = True

@dataclass(kw_only=True)
class Product(Entity):
    name: str
    description: str
    base_price: Money
    category_id: uuid.UUID
    modifier_groups: list[ModifierGroup] = field(default_factory=list)
    is_active: bool = True

    def calculate_price(
        self,
        selected_modifiers: dict[uuid.UUID, list[uuid.UUID]],
        product_price_override: Money | None = None,
        modifier_price_overrides: dict[uuid.UUID, Money] | None = None
    ) -> Money:
        """
        Calculates the price of the product given a mapping of:
        ModifierGroup ID -> List of ModifierOption IDs
        Optionally accepts base price and modifier price overrides.
        """
        modifier_price_overrides = modifier_price_overrides or {}
        total = product_price_override if product_price_override is not None else self.base_price
        for group in self.modifier_groups:
            if group.id in selected_modifiers:
                # We assume validation has already passed (or will fail nicely if opt not found)
                opts = [opt for opt in group.options if opt.id in selected_modifiers[group.id]]
                for opt in opts:
                    if opt.id in modifier_price_overrides:
                        total += modifier_price_overrides[opt.id]
                    else:
                        total += opt.price_adjustment
        return total
