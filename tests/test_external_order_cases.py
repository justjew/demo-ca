import uuid
import pytest
from datetime import datetime
from unittest.mock import MagicMock

from domain.use_cases.external_order_cases import AcceptExternalOrderUseCase
from domain.entities.order import Order, OrderItem
from domain.entities.outlet import Outlet
from domain.value_objects import Money, DeliveryMethod

@pytest.fixture
def order_repo_mock():
    return MagicMock()

@pytest.fixture
def outlet_repo_mock():
    return MagicMock()

@pytest.fixture
def external_gateway_mock():
    return MagicMock()

@pytest.fixture
def event_dispatcher_mock():
    return MagicMock()

@pytest.fixture
def use_case(order_repo_mock, outlet_repo_mock, external_gateway_mock, event_dispatcher_mock):
    return AcceptExternalOrderUseCase(
        order_repo=order_repo_mock,
        outlet_repo=outlet_repo_mock,
        external_order_gateway=external_gateway_mock,
        event_dispatcher=event_dispatcher_mock
    )

def test_accept_external_order_success(use_case, outlet_repo_mock, external_gateway_mock, order_repo_mock, event_dispatcher_mock):
    current_dt = datetime.now()
    payload = {"ext_id": "123", "items": []}
    
    order_mock = Order(
        client_id=uuid.uuid4(),
        outlet_id=uuid.uuid4(),
        items=[OrderItem(product_id=uuid.uuid4(), quantity=1, price=Money(amount=100, currency="USD"))],
        delivery_method=DeliveryMethod.DELIVERY,
        external_id="123"
    )
    order_mock.total_amount = Money(amount=100, currency="USD")
    external_gateway_mock.parse_incoming_payload.return_value = order_mock
    
    outlet_mock = MagicMock(spec=Outlet)
    outlet_mock.is_product_available.return_value = True
    outlet_repo_mock.get_by_id.return_value = outlet_mock
    
    order = use_case.execute(payload, current_dt)
    
    assert order == order_mock
    order_repo_mock.save.assert_called_once_with(order_mock)
    
    event_dispatcher_mock.assert_called_once()
    event = event_dispatcher_mock.call_args[0][0]
    assert event.order_id == order_mock.id
    assert event.total_amount == 100
