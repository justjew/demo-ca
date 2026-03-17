import uuid

from ..entities.catalog import Product
from ..entities.company import Company
from ..entities.outlet import Outlet
from ..value_objects import Money


class PricingService:
    """Domain service responsible for complex pricing rules."""

    @staticmethod
    def calculate_order_item_price(
        product: Product,
        selected_modifiers: dict[uuid.UUID, list[uuid.UUID]],
        outlet: Outlet | None = None,
    ) -> Money:
        """Calculates the unit price for a given product and its modifiers."""
        product_override = (
            outlet.product_price_overrides.get(product.id) if outlet else None
        )
        modifier_overrides = outlet.modifier_price_overrides if outlet else None
        return product.calculate_price(
            selected_modifiers,
            product_price_override=product_override,
            modifier_price_overrides=modifier_overrides,
        )

    @staticmethod
    def calculate_max_loyalty_discount(order_total: Money, company: Company) -> int:
        """
        Calculates the maximum amount (in minor units) that can be paid with loyalty points
        based on the company's rules.
        """
        max_discount_amount = int(
            order_total.amount * company.max_loyalty_payment_percent
        )
        return max_discount_amount
