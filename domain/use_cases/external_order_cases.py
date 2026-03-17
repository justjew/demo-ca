from collections.abc import Callable
from datetime import datetime
from typing import Any

from ..entities.order import Order
from ..events import OrderCreatedEvent
from ..interfaces.gateways import IExternalOrderGateway
from ..interfaces.repositories import IOrderRepository, IOutletRepository


class AcceptExternalOrderUseCase:
    def __init__(
        self,
        order_repo: IOrderRepository,
        outlet_repo: IOutletRepository,
        external_order_gateway: IExternalOrderGateway,
        event_dispatcher: Callable[[Any], None]
    ):
        self.order_repo = order_repo
        self.outlet_repo = outlet_repo
        self.external_order_gateway = external_order_gateway
        self.event_dispatcher = event_dispatcher

    def execute(self, payload: dict[str, Any], current_dt: datetime) -> Order:
        order = self.external_order_gateway.parse_incoming_payload(payload)

        outlet = self.outlet_repo.get_by_id(order.outlet_id)
        if not outlet:
            raise ValueError("Outlet not found")

        # Basic validations for aggregator orders
        outlet.validate_can_order(current_dt)

        for item in order.items:
            # We only validate availability, we ignore pricing rules since aggregator gives us the final valid price
            if not outlet.is_product_available(item.product_id):
                raise ValueError(f"Product {item.product_id} is unavailable")

        # Usually, aggregator orders are already "accepted" or "awaiting payment" but
        # here we just rely on whatever status the gateway set, or we default to CREATED.

        self.order_repo.save(order)

        self.event_dispatcher(
            OrderCreatedEvent(
                occurred_on=current_dt,
                order_id=order.id,
                client_id=order.client_id,
                outlet_id=order.outlet_id,
                total_amount=order.total_amount.amount if order.total_amount else 0
            )
        )

        return order
