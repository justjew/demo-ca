import uuid
from dataclasses import dataclass
from datetime import datetime

from .value_objects import OrderStatus


@dataclass
class DomainEvent:
    occurred_on: datetime

@dataclass
class OrderCreatedEvent(DomainEvent):
    order_id: uuid.UUID
    client_id: uuid.UUID | None
    outlet_id: uuid.UUID
    total_amount: int # minor units

@dataclass
class OrderStatusChangedEvent(DomainEvent):
    order_id: uuid.UUID
    old_status: OrderStatus
    new_status: OrderStatus

@dataclass
class LoyaltyPointsAccruedEvent(DomainEvent):
    client_id: uuid.UUID
    company_id: uuid.UUID
    points_added: int
    order_id: uuid.UUID
