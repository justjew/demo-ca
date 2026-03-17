import uuid
from dataclasses import dataclass, field
from datetime import datetime

from ..exceptions import EmptyCartError, InvalidStateTransitionError
from ..value_objects import Address, DeliveryMethod, Money, OrderStatus
from .base import Entity


@dataclass(kw_only=True)
class CartItem(Entity):
    product_id: uuid.UUID
    quantity: int
    selected_modifiers: dict[uuid.UUID, list[uuid.UUID]] = field(default_factory=dict)

@dataclass(kw_only=True)
class Cart(Entity):
    client_id: uuid.UUID | None
    outlet_id: uuid.UUID
    items: list[CartItem] = field(default_factory=list)

    def is_empty(self) -> bool:
        return len(self.items) == 0

@dataclass(kw_only=True)
class OrderItem(Entity):
    product_id: uuid.UUID
    quantity: int
    price: Money  # Unit price at the time of order creation (includes modifiers)
    selected_modifiers: dict[uuid.UUID, list[uuid.UUID]] = field(default_factory=dict)

    def get_total(self) -> Money:
        return self.price * self.quantity

@dataclass(kw_only=True)
class Order(Entity):
    client_id: uuid.UUID | None
    outlet_id: uuid.UUID
    items: list[OrderItem]
    delivery_method: DeliveryMethod
    status: OrderStatus = OrderStatus.CREATED

    delivery_address: Address | None = None
    scheduled_time: datetime | None = None
    applied_loyalty_points: int = 0
    total_amount: Money | None = None # Calculated total including points deduction

    receipt_id: str | None = None
    delivery_tracking_id: str | None = None
    external_id: str | None = None

    def calculate_total(self) -> None:
        """Helper to compute basic total. Note: Pricing service normally does complex math."""
        if not self.items:
            raise EmptyCartError("Cannot have an order with no items.")

        base_currency = self.items[0].price.currency
        total = Money(amount=0, currency=base_currency)
        for item in self.items:
            total += item.get_total()

        # Loyalty points assumed to equal 1:1 minor currency unit for this context
        if self.applied_loyalty_points > 0:
            discount = Money(amount=self.applied_loyalty_points, currency=base_currency)
            if discount > total:
                # If discount is greater than total, just set to zero or leave small amount
                # The exact rule depends on Company config. We'll set it to 0.
                total = Money(amount=0, currency=base_currency)
            else:
                total -= discount

        self.total_amount = total

    def change_status(self, new_status: OrderStatus) -> None:
        valid_transitions = {
            OrderStatus.CREATED: [OrderStatus.AWAITING_PAYMENT, OrderStatus.CANCELED],
            OrderStatus.AWAITING_PAYMENT: [OrderStatus.ACCEPTED, OrderStatus.CANCELED],
            OrderStatus.ACCEPTED: [OrderStatus.READY, OrderStatus.CANCELED],
            OrderStatus.READY: [OrderStatus.TRANSFERRED, OrderStatus.COMPLETED],
            OrderStatus.TRANSFERRED: [OrderStatus.COMPLETED],
            OrderStatus.COMPLETED: [],
            OrderStatus.CANCELED: []
        }

        allowed = valid_transitions.get(self.status, [])
        if new_status not in allowed:
            raise InvalidStateTransitionError(f"Cannot transition order from {self.status.value} to {new_status.value}")

        self.status = new_status
