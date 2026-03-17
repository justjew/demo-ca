import uuid
from abc import ABC, abstractmethod
from typing import Any

from ..entities.order import Order
from ..value_objects import Address


class IPaymentGateway(ABC):
    @abstractmethod
    def process_payment(self, order_id: uuid.UUID, amount: int, currency: str) -> bool:
        """Processes payment and returns True if successful."""
        pass

    @abstractmethod
    def refund_payment(self, order_id: uuid.UUID, amount: int, currency: str) -> bool:
        pass


class ILogisticsGateway(ABC):
    @abstractmethod
    def request_courier(
        self, order_id: uuid.UUID, pickup_address: Address, dropoff_address: Address
    ) -> str:
        """Requests courier and returns a tracking ID."""
        pass

    @abstractmethod
    def get_delivery_status(self, tracking_id: str) -> str:
        pass


class IFiscalGateway(ABC):
    @abstractmethod
    def generate_receipt(self, order: Order) -> str:
        """Generates fiscal receipt and returns its URL/ID."""
        pass


class IExternalOrderGateway(ABC):
    @abstractmethod
    def parse_incoming_payload(self, payload: dict[str, Any]) -> Order:
        """Transforms an external aggregator's order format into internal representation."""
        pass
