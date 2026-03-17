from ..entities.company import Company
from ..value_objects import Money


class LoyaltyService:
    """Domain service for advanced loyalty logic."""

    @staticmethod
    def calculate_accrual(order_total: Money, company: Company, total_spent: int = 0, spent_points: int = 0) -> int:
        """
        Calculates how many points should be awarded for an order.
        Usually points are only awarded for the portion of the order paid with actual money.
        """
        paid_amount = order_total.amount - spent_points
        if paid_amount <= 0:
            return 0

        rate = company.get_loyalty_accrual_rate_for_spent(total_spent)
        return int(paid_amount * rate)
