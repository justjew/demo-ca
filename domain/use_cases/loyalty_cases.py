import uuid
from collections.abc import Callable
from datetime import datetime
from typing import Any

from ..events import LoyaltyPointsAccruedEvent
from ..interfaces.repositories import (
    IClientRepository,
    ICompanyRepository,
    IOrderRepository,
)
from ..services.loyalty_service import LoyaltyService


class CalculateAccrualUseCase:
    """This use case could be fired by a DomainEvent listener when Order completes."""

    def __init__(
        self,
        order_repo: IOrderRepository,
        client_repo: IClientRepository,
        company_repo: ICompanyRepository,
        event_dispatcher: Callable[[Any], None]
    ):
        self.order_repo = order_repo
        self.client_repo = client_repo
        self.company_repo = company_repo
        self.event_dispatcher = event_dispatcher

    def execute(self, order_id: uuid.UUID, current_dt: datetime) -> None:
        order = self.order_repo.get_by_id(order_id)
        if not order:
            return

        if not order.client_id:
            return  # Guest checkout, no point accrual

        profile = self.client_repo.get_loyalty_profile(order.client_id, order.outlet_id)
        if not profile:
            return

        company = self.company_repo.get_by_id(profile.company_id) # Using profile's reference or resolving via outlet
        if not company:
            return

        if order.total_amount is None:
            return

        points_to_add = LoyaltyService.calculate_accrual(order.total_amount, company, total_spent=profile.total_spent, spent_points=0)
        if points_to_add > 0:
            profile.add_points(points_to_add)
            profile.total_spent += order.total_amount.amount
            self.client_repo.save_loyalty_profile(profile)

            self.event_dispatcher(
                LoyaltyPointsAccruedEvent(
                    occurred_on=current_dt,
                    client_id=order.client_id,
                    company_id=profile.company_id,
                    points_added=points_to_add,
                    order_id=order.id
                )
            )
