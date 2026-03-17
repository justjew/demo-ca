import uuid

from ..entities.catalog import Product
from ..entities.company import Company
from ..value_objects import Money


class PricingService:
    """Domain service responsible for complex pricing rules."""

    @staticmethod
    def calculate_order_item_price(product: Product, selected_modifiers: dict[uuid.UUID, list[uuid.UUID]]) -> Money:
        """Calculates the unit price for a given product and its modifiers."""
        return product.calculate_price(selected_modifiers)

    @staticmethod
    def calculate_max_loyalty_discount(order_total: Money, company: Company) -> int:
        """
        Calculates the maximum amount (in minor units) that can be paid with loyalty points
        based on the company's rules.
        """
        max_discount_amount = int(order_total.amount * company.max_loyalty_payment_percent)
        return max_discount_amount
