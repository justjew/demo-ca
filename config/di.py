import uuid
from typing import Any

from adapters.db.django_orm.repositories import (
    DjangoClientRepository,
    DjangoCompanyRepository,
    DjangoOrderRepository,
    DjangoOutletRepository,
    DjangoProductRepository,
)
from domain.entities.order import Order, OrderItem
from domain.interfaces.gateways import (
    IExternalOrderGateway,
    IFiscalGateway,
    ILogisticsGateway,
    IPaymentGateway,
)
from domain.use_cases.catalog_cases import (
    ConfigureModifiersUseCase,
    ManageStopListUseCase,
    ProductCrudUseCase,
)
from domain.use_cases.client_cases import ClientCrudUseCase
from domain.use_cases.company_cases import CompanyCrudUseCase
from domain.use_cases.external_order_cases import AcceptExternalOrderUseCase
from domain.use_cases.loyalty_cases import CalculateAccrualUseCase
from domain.use_cases.order_cases import (
    ChangeOrderStatusUseCase,
    CreateOrderUseCase,
    ProcessPaymentUseCase,
)
from domain.use_cases.outlet_cases import OutletCrudUseCase
from domain.value_objects import Address, DeliveryMethod, Money, OrderStatus


# Dummy gateways for demonstration
class DummyLogisticsGateway(ILogisticsGateway):
    def request_courier(
        self, order_id: uuid.UUID, pickup_address: Address, dropoff_address: Address
    ) -> str:
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


class DummyExternalOrderGateway(IExternalOrderGateway):
    def parse_incoming_payload(self, payload: dict[str, Any]) -> Order:
        items = []
        for item_data in payload.get("items", []):
            selected_modifiers = {
                uuid.UUID(k): [uuid.UUID(uid) for uid in v]
                for k, v in item_data.get("selected_modifiers", {}).items()
            }
            items.append(
                OrderItem(
                    product_id=uuid.UUID(item_data["product_id"]),
                    quantity=item_data["quantity"],
                    price=Money(
                        amount=item_data["price_amount"],
                        currency=item_data["price_currency"],
                    ),
                    selected_modifiers=selected_modifiers,
                )
            )

        address_data = payload.get("delivery_address")
        delivery_address = Address(**address_data) if address_data else None

        return Order(
            client_id=uuid.UUID(payload["client_id"])
            if payload.get("client_id")
            else None,
            outlet_id=uuid.UUID(payload["outlet_id"]),
            items=items,
            delivery_method=DeliveryMethod(payload["delivery_method"]),
            status=OrderStatus.CREATED,
            delivery_address=delivery_address,
            external_id=payload.get("external_id"),
        )


def dummy_event_dispatcher(event: Any) -> None:
    print(f"Domain Event Dispatched: {event}")


class Container:
    """Simple Composition Root for injecting dependencies."""

    # --- Repositories ---

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

    # --- CRUD Use Cases (one per entity) ---

    @classmethod
    def get_client_crud(cls):
        return ClientCrudUseCase(client_repo=cls.get_client_repo())

    @classmethod
    def get_company_crud(cls):
        return CompanyCrudUseCase(repo=cls.get_company_repo())

    @classmethod
    def get_outlet_crud(cls):
        return OutletCrudUseCase(repo=cls.get_outlet_repo())

    @classmethod
    def get_product_crud(cls):
        return ProductCrudUseCase(repo=cls.get_product_repo())

    # --- Domain-specific Use Cases ---

    @classmethod
    def get_manage_stop_list_use_case(cls):
        return ManageStopListUseCase(outlet_repo=cls.get_outlet_repo())

    @classmethod
    def get_create_order_use_case(cls):
        return CreateOrderUseCase(
            order_repo=cls.get_order_repo(),
            outlet_repo=cls.get_outlet_repo(),
            product_repo=cls.get_product_repo(),
            client_repo=cls.get_client_repo(),
            company_repo=cls.get_company_repo(),
            event_dispatcher=dummy_event_dispatcher,
        )

    @classmethod
    def get_change_order_status_use_case(cls):
        return ChangeOrderStatusUseCase(
            order_repo=cls.get_order_repo(),
            event_dispatcher=dummy_event_dispatcher,
            logistics_gateway=DummyLogisticsGateway(),
        )

    @classmethod
    def get_process_payment_use_case(cls):
        return ProcessPaymentUseCase(
            order_repo=cls.get_order_repo(),
            payment_gateway=DummyPaymentGateway(),
            fiscal_gateway=DummyFiscalGateway(),
            event_dispatcher=dummy_event_dispatcher,
        )

    @classmethod
    def get_configure_modifiers_use_case(cls):
        return ConfigureModifiersUseCase(product_repo=cls.get_product_repo())

    @classmethod
    def get_accept_external_order_use_case(cls):
        return AcceptExternalOrderUseCase(
            order_repo=cls.get_order_repo(),
            outlet_repo=cls.get_outlet_repo(),
            external_order_gateway=DummyExternalOrderGateway(),
            event_dispatcher=dummy_event_dispatcher,
        )

    @classmethod
    def get_calculate_accrual_use_case(cls):
        return CalculateAccrualUseCase(
            order_repo=cls.get_order_repo(),
            client_repo=cls.get_client_repo(),
            company_repo=cls.get_company_repo(),
            event_dispatcher=dummy_event_dispatcher,
        )
