import uuid
from typing import Any

from adapters.db.django_orm.repositories import (
    DjangoClientRepository,
    DjangoCompanyRepository,
    DjangoOrderRepository,
    DjangoOutletRepository,
    DjangoProductRepository,
)
from domain.interfaces.gateways import (
    IFiscalGateway,
    ILogisticsGateway,
    IPaymentGateway,
)
from domain.use_cases.catalog_cases import ManageStopListUseCase
from domain.use_cases.order_cases import (
    ChangeOrderStatusUseCase,
    CreateOrderUseCase,
    ProcessPaymentUseCase,
)
from domain.value_objects import Address


# Dummy gateways for demonstration
class DummyLogisticsGateway(ILogisticsGateway):
    def request_courier(self, order_id: uuid.UUID, pickup_address: Address, dropoff_address: Address) -> str:
        return "tracking-123"

    def get_delivery_status(self, tracking_id: str) -> str:
        return "DELIVERED"

class DummyPaymentGateway(IPaymentGateway):
    def process_payment(self, order_id: uuid.UUID, amount: int, currency: str) -> bool:
        return True

    def refund_payment(self, order_id: uuid.UUID, amount: int, currency: str) -> bool:
        return True

class DummyFiscalGateway(IFiscalGateway):
    def generate_receipt(self, order) -> str:
        return "receipt-123"

def dummy_event_dispatcher(event: Any) -> None:
    print(f"Domain Event Dispatched: {event}")


class Container:
    """Simple Composition Root for injecting dependencies."""

    @classmethod
    def get_company_repo(cls):
        return DjangoCompanyRepository()

    @classmethod
    def get_outlet_repo(cls):
        return DjangoOutletRepository()

    @classmethod
    def get_product_repo(cls):
        return DjangoProductRepository()

    @classmethod
    def get_client_repo(cls):
        return DjangoClientRepository()

    @classmethod
    def get_order_repo(cls):
        return DjangoOrderRepository()

    @classmethod
    def get_manage_stop_list_use_case(cls):
        return ManageStopListUseCase(
            outlet_repo=cls.get_outlet_repo()
        )

    @classmethod
    def get_create_order_use_case(cls):
        return CreateOrderUseCase(
            order_repo=cls.get_order_repo(),
            outlet_repo=cls.get_outlet_repo(),
            product_repo=cls.get_product_repo(),
            client_repo=cls.get_client_repo(),
            company_repo=cls.get_company_repo(),
            event_dispatcher=dummy_event_dispatcher
        )

    @classmethod
    def get_change_order_status_use_case(cls):
        return ChangeOrderStatusUseCase(
            order_repo=cls.get_order_repo(),
            event_dispatcher=dummy_event_dispatcher,
            logistics_gateway=DummyLogisticsGateway()
        )

    @classmethod
    def get_process_payment_use_case(cls):
        return ProcessPaymentUseCase(
            order_repo=cls.get_order_repo(),
            payment_gateway=DummyPaymentGateway(),
            fiscal_gateway=DummyFiscalGateway(),
            event_dispatcher=dummy_event_dispatcher
        )
