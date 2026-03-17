import uuid
import pytest
from datetime import datetime
from unittest.mock import MagicMock

from domain.use_cases.order_cases import CreateOrderUseCase, ChangeOrderStatusUseCase
from domain.entities.order import Cart, CartItem, Order, OrderItem
from domain.entities.catalog import Product, ModifierGroup
from domain.entities.client import LoyaltyProfile
from domain.entities.company import Company
from domain.entities.outlet import Outlet
from domain.value_objects import Address, DeliveryMethod, Money, OrderStatus
from domain.exceptions import (
    DeliveryNotAvailableError,
    InsufficientPointsError,
    InvalidModifierError,
    ProductInStopListError,
    EmptyCartError,
    InvalidStateTransitionError
)

@pytest.fixture
def order_repo_mock():
    return MagicMock()

@pytest.fixture
def outlet_repo_mock():
    return MagicMock()

@pytest.fixture
def product_repo_mock():
    return MagicMock()

@pytest.fixture
def client_repo_mock():
    return MagicMock()

@pytest.fixture
def company_repo_mock():
    return MagicMock()

@pytest.fixture
def event_dispatcher_mock():
    return MagicMock()

@pytest.fixture
def create_order_use_case(order_repo_mock, outlet_repo_mock, product_repo_mock, client_repo_mock, company_repo_mock, event_dispatcher_mock):
    return CreateOrderUseCase(
        order_repo=order_repo_mock,
        outlet_repo=outlet_repo_mock,
        product_repo=product_repo_mock,
        client_repo=client_repo_mock,
        company_repo=company_repo_mock,
        event_dispatcher=event_dispatcher_mock
    )

@pytest.fixture
def change_status_use_case(order_repo_mock, event_dispatcher_mock):
    return ChangeOrderStatusUseCase(
        order_repo=order_repo_mock,
        event_dispatcher=event_dispatcher_mock
    )

def test_create_order_empty_cart(create_order_use_case):
    cart = Cart(client_id=uuid.uuid4(), outlet_id=uuid.uuid4(), items=[])
    with pytest.raises(ValueError, match="Cart is empty"):
        create_order_use_case.execute(cart, DeliveryMethod.PICKUP, datetime.now())

def test_create_order_missing_client_id(create_order_use_case):
    cart_item = CartItem(product_id=uuid.uuid4(), quantity=1)
    cart = Cart(client_id=None, outlet_id=uuid.uuid4(), items=[cart_item])
    with pytest.raises(ValueError, match="Client ID is required for order creation"):
        create_order_use_case.execute(cart, DeliveryMethod.PICKUP, datetime.now())

def test_create_order_outlet_not_found(create_order_use_case, outlet_repo_mock):
    cart_item = CartItem(product_id=uuid.uuid4(), quantity=1)
    cart = Cart(client_id=uuid.uuid4(), outlet_id=uuid.uuid4(), items=[cart_item])
    outlet_repo_mock.get_by_id.return_value = None
    
    with pytest.raises(ValueError, match="Outlet not found"):
        create_order_use_case.execute(cart, DeliveryMethod.PICKUP, datetime.now())

def test_create_order_company_not_found(create_order_use_case, outlet_repo_mock, company_repo_mock):
    cart_item = CartItem(product_id=uuid.uuid4(), quantity=1)
    cart = Cart(client_id=uuid.uuid4(), outlet_id=uuid.uuid4(), items=[cart_item])
    
    outlet_mock = MagicMock(spec=Outlet)
    outlet_mock.company_id = uuid.uuid4()
    outlet_repo_mock.get_by_id.return_value = outlet_mock
    
    company_repo_mock.get_by_id.return_value = None
    
    with pytest.raises(ValueError, match="Company not found"):
        create_order_use_case.execute(cart, DeliveryMethod.PICKUP, datetime.now())

def test_create_order_delivery_address_missing(create_order_use_case, outlet_repo_mock, company_repo_mock):
    cart_item = CartItem(product_id=uuid.uuid4(), quantity=1)
    cart = Cart(client_id=uuid.uuid4(), outlet_id=uuid.uuid4(), items=[cart_item])
    
    outlet_mock = MagicMock(spec=Outlet)
    outlet_mock.company_id = uuid.uuid4()
    outlet_repo_mock.get_by_id.return_value = outlet_mock
    
    company_mock = MagicMock(spec=Company)
    company_repo_mock.get_by_id.return_value = company_mock
    
    with pytest.raises(ValueError, match="Delivery address is required for delivery"):
        create_order_use_case.execute(cart, DeliveryMethod.DELIVERY, datetime.now())

def test_create_order_delivery_not_available(create_order_use_case, outlet_repo_mock, company_repo_mock, monkeypatch):
    cart_item = CartItem(product_id=uuid.uuid4(), quantity=1)
    cart = Cart(client_id=uuid.uuid4(), outlet_id=uuid.uuid4(), items=[cart_item])
    
    outlet_mock = MagicMock(spec=Outlet)
    outlet_mock.company_id = uuid.uuid4()
    outlet_repo_mock.get_by_id.return_value = outlet_mock
    
    company_mock = MagicMock(spec=Company)
    company_repo_mock.get_by_id.return_value = company_mock
    
    address = Address(city="Test City", street="Test St", building="1A")
    
    is_address_covered_mock = MagicMock(return_value=False)
    monkeypatch.setattr('domain.services.delivery_service.DeliveryService.is_address_covered', is_address_covered_mock)
    
    with pytest.raises(DeliveryNotAvailableError, match="Address is outside delivery zone"):
        create_order_use_case.execute(cart, DeliveryMethod.DELIVERY, datetime.now(), delivery_address=address)

def test_create_order_product_in_stop_list(create_order_use_case, outlet_repo_mock, company_repo_mock):
    product_id = uuid.uuid4()
    cart_item = CartItem(product_id=product_id, quantity=1)
    cart = Cart(client_id=uuid.uuid4(), outlet_id=uuid.uuid4(), items=[cart_item])
    
    outlet_mock = MagicMock(spec=Outlet)
    outlet_mock.company_id = uuid.uuid4()
    outlet_mock.is_product_available.return_value = False
    outlet_repo_mock.get_by_id.return_value = outlet_mock
    
    company_mock = MagicMock(spec=Company)
    company_repo_mock.get_by_id.return_value = company_mock
    
    with pytest.raises(ProductInStopListError, match=f"Product {product_id} is unavailable"):
        create_order_use_case.execute(cart, DeliveryMethod.PICKUP, datetime.now())

def test_create_order_modifier_in_stop_list(create_order_use_case, outlet_repo_mock, company_repo_mock):
    product_id = uuid.uuid4()
    modifier_id = uuid.uuid4()
    cart_item = CartItem(product_id=product_id, quantity=1, selected_modifiers={uuid.uuid4(): [modifier_id]})
    cart = Cart(client_id=uuid.uuid4(), outlet_id=uuid.uuid4(), items=[cart_item])
    
    outlet_mock = MagicMock(spec=Outlet)
    outlet_mock.company_id = uuid.uuid4()
    outlet_mock.is_product_available.return_value = True
    outlet_mock.is_modifier_available.return_value = False
    outlet_repo_mock.get_by_id.return_value = outlet_mock
    
    company_mock = MagicMock(spec=Company)
    company_repo_mock.get_by_id.return_value = company_mock
    
    with pytest.raises(ProductInStopListError, match=f"Modifier {modifier_id} is unavailable"):
        create_order_use_case.execute(cart, DeliveryMethod.PICKUP, datetime.now())

def test_create_order_product_not_found(create_order_use_case, outlet_repo_mock, company_repo_mock, product_repo_mock):
    product_id = uuid.uuid4()
    cart_item = CartItem(product_id=product_id, quantity=1)
    cart = Cart(client_id=uuid.uuid4(), outlet_id=uuid.uuid4(), items=[cart_item])
    
    outlet_mock = MagicMock(spec=Outlet)
    outlet_mock.company_id = uuid.uuid4()
    outlet_mock.is_product_available.return_value = True
    outlet_repo_mock.get_by_id.return_value = outlet_mock
    
    company_mock = MagicMock(spec=Company)
    company_repo_mock.get_by_id.return_value = company_mock
    
    product_repo_mock.get_by_id.return_value = None
    
    with pytest.raises(ValueError, match=f"Product {product_id} not found"):
        create_order_use_case.execute(cart, DeliveryMethod.PICKUP, datetime.now())

def test_create_order_invalid_modifiers(create_order_use_case, outlet_repo_mock, company_repo_mock, product_repo_mock):
    product_id = uuid.uuid4()
    group_id = uuid.uuid4()
    cart_item = CartItem(product_id=product_id, quantity=1, selected_modifiers={group_id: [uuid.uuid4()]})
    cart = Cart(client_id=uuid.uuid4(), outlet_id=uuid.uuid4(), items=[cart_item])
    
    outlet_mock = MagicMock(spec=Outlet)
    outlet_mock.company_id = uuid.uuid4()
    outlet_mock.is_product_available.return_value = True
    outlet_mock.is_modifier_available.return_value = True
    outlet_repo_mock.get_by_id.return_value = outlet_mock
    
    company_mock = MagicMock(spec=Company)
    company_repo_mock.get_by_id.return_value = company_mock
    
    product_mock = MagicMock(spec=Product)
    group_mock = MagicMock(spec=ModifierGroup)
    group_mock.id = group_id
    group_mock.name = "Test Group"
    group_mock.validate_selection.return_value = False
    product_mock.modifier_groups = [group_mock]
    product_repo_mock.get_by_id.return_value = product_mock
    
    with pytest.raises(InvalidModifierError, match=f"Modifier constraints violated for group {group_mock.name}"):
        create_order_use_case.execute(cart, DeliveryMethod.PICKUP, datetime.now())

def test_create_order_success(create_order_use_case, outlet_repo_mock, company_repo_mock, product_repo_mock, order_repo_mock, event_dispatcher_mock, monkeypatch):
    client_id = uuid.uuid4()
    product_id = uuid.uuid4()
    cart_item = CartItem(product_id=product_id, quantity=2)
    cart = Cart(client_id=client_id, outlet_id=uuid.uuid4(), items=[cart_item])
    
    outlet_mock = MagicMock(spec=Outlet)
    outlet_mock.company_id = uuid.uuid4()
    outlet_mock.is_product_available.return_value = True
    outlet_repo_mock.get_by_id.return_value = outlet_mock
    
    company_mock = MagicMock(spec=Company)
    company_repo_mock.get_by_id.return_value = company_mock
    
    product_mock = MagicMock(spec=Product)
    product_mock.modifier_groups = []
    product_repo_mock.get_by_id.return_value = product_mock
    
    unit_price = Money(amount=100, currency="USD")
    calculate_order_item_price_mock = MagicMock(return_value=unit_price)
    monkeypatch.setattr('domain.services.pricing_service.PricingService.calculate_order_item_price', calculate_order_item_price_mock)
    
    current_dt = datetime.now()
    
    order = create_order_use_case.execute(cart, DeliveryMethod.PICKUP, current_dt)
    
    assert order.client_id == client_id
    assert order.items[0].product_id == product_id
    assert order.items[0].quantity == 2
    assert order.items[0].price == unit_price
    assert order.total_amount.amount == 200
    
    order_repo_mock.save.assert_called_once_with(order)
    event_dispatcher_mock.assert_called_once()
    event = event_dispatcher_mock.call_args[0][0]
    assert event.order_id == order.id
    assert event.total_amount == 200

def test_create_order_spend_points_success(create_order_use_case, outlet_repo_mock, company_repo_mock, product_repo_mock, client_repo_mock, monkeypatch):
    client_id = uuid.uuid4()
    product_id = uuid.uuid4()
    cart_item = CartItem(product_id=product_id, quantity=2)
    cart = Cart(client_id=client_id, outlet_id=uuid.uuid4(), items=[cart_item])
    
    outlet_mock = MagicMock(spec=Outlet)
    outlet_mock.company_id = uuid.uuid4()
    outlet_mock.is_product_available.return_value = True
    outlet_repo_mock.get_by_id.return_value = outlet_mock
    
    company_mock = MagicMock(spec=Company)
    company_repo_mock.get_by_id.return_value = company_mock
    
    product_mock = MagicMock(spec=Product)
    product_mock.modifier_groups = []
    product_repo_mock.get_by_id.return_value = product_mock
    
    unit_price = Money(amount=100, currency="USD")
    calculate_order_item_price_mock = MagicMock(return_value=unit_price)
    monkeypatch.setattr('domain.services.pricing_service.PricingService.calculate_order_item_price', calculate_order_item_price_mock)
    
    profile_mock = MagicMock(spec=LoyaltyProfile)
    client_repo_mock.get_loyalty_profile.return_value = profile_mock
    
    calculate_max_loyalty_discount_mock = MagicMock(return_value=50)
    monkeypatch.setattr('domain.services.pricing_service.PricingService.calculate_max_loyalty_discount', calculate_max_loyalty_discount_mock)
    
    current_dt = datetime.now()
    
    order = create_order_use_case.execute(cart, DeliveryMethod.PICKUP, current_dt, spend_points=100)
    
    # max discount is 50, so point spend is capped at 50
    assert order.applied_loyalty_points == 50
    assert order.total_amount.amount == 150 # 200 total - 50 discount
    
    profile_mock.spend_points.assert_called_once_with(50)
    client_repo_mock.save_loyalty_profile.assert_called_once_with(profile_mock)

def test_create_order_insufficient_points(create_order_use_case, outlet_repo_mock, company_repo_mock, product_repo_mock, client_repo_mock, monkeypatch):
    client_id = uuid.uuid4()
    product_id = uuid.uuid4()
    cart_item = CartItem(product_id=product_id, quantity=2)
    cart = Cart(client_id=client_id, outlet_id=uuid.uuid4(), items=[cart_item])
    
    outlet_mock = MagicMock(spec=Outlet)
    outlet_mock.company_id = uuid.uuid4()
    outlet_mock.is_product_available.return_value = True
    outlet_repo_mock.get_by_id.return_value = outlet_mock
    
    company_mock = MagicMock(spec=Company)
    company_repo_mock.get_by_id.return_value = company_mock
    
    product_mock = MagicMock(spec=Product)
    product_mock.modifier_groups = []
    product_repo_mock.get_by_id.return_value = product_mock
    
    unit_price = Money(amount=100, currency="USD")
    calculate_order_item_price_mock = MagicMock(return_value=unit_price)
    monkeypatch.setattr('domain.services.pricing_service.PricingService.calculate_order_item_price', calculate_order_item_price_mock)
    
    client_repo_mock.get_loyalty_profile.return_value = None
    
    with pytest.raises(InsufficientPointsError, match="Client has no profile for this company"):
        create_order_use_case.execute(cart, DeliveryMethod.PICKUP, datetime.now(), spend_points=10)


def test_change_order_status_success(change_status_use_case, order_repo_mock, event_dispatcher_mock):
    order_id = uuid.uuid4()
    order_mock = MagicMock(spec=Order)
    order_mock.id = order_id
    order_mock.status = OrderStatus.CREATED
    order_repo_mock.get_by_id.return_value = order_mock
    
    current_dt = datetime.now()
    
    change_status_use_case.execute(order_id, OrderStatus.AWAITING_PAYMENT, current_dt)
    
    order_mock.change_status.assert_called_once_with(OrderStatus.AWAITING_PAYMENT)
    order_repo_mock.save.assert_called_once_with(order_mock)
    
    event_dispatcher_mock.assert_called_once()
    event = event_dispatcher_mock.call_args[0][0]
    assert event.order_id == order_mock.id
    assert event.old_status == OrderStatus.CREATED
    assert event.new_status == OrderStatus.AWAITING_PAYMENT

def test_change_order_status_not_found(change_status_use_case, order_repo_mock):
    order_id = uuid.uuid4()
    order_repo_mock.get_by_id.return_value = None
    
    with pytest.raises(ValueError, match="Order not found"):
        change_status_use_case.execute(order_id, OrderStatus.AWAITING_PAYMENT, datetime.now())


def test_create_order_product_not_in_assortment(create_order_use_case, outlet_repo_mock, company_repo_mock):
    product_id = uuid.uuid4()
    cart_item = CartItem(product_id=product_id, quantity=1)
    cart = Cart(client_id=uuid.uuid4(), outlet_id=uuid.uuid4(), items=[cart_item])
    
    outlet_mock = MagicMock(spec=Outlet)
    outlet_mock.company_id = uuid.uuid4()
    outlet_mock.is_in_assortment.return_value = False
    outlet_repo_mock.get_by_id.return_value = outlet_mock
    
    company_mock = MagicMock(spec=Company)
    company_repo_mock.get_by_id.return_value = company_mock
    
    with pytest.raises(ProductInStopListError, match=f"Product {product_id} is not in local assortment"):
        create_order_use_case.execute(cart, DeliveryMethod.PICKUP, datetime.now())

def test_create_order_with_price_overrides(create_order_use_case, outlet_repo_mock, company_repo_mock, product_repo_mock, order_repo_mock, event_dispatcher_mock):
    client_id = uuid.uuid4()
    product_id = uuid.uuid4()
    modifier_id = uuid.uuid4()
    group_id = uuid.uuid4()
    cart_item = CartItem(product_id=product_id, quantity=1, selected_modifiers={group_id: [modifier_id]})
    cart = Cart(client_id=client_id, outlet_id=uuid.uuid4(), items=[cart_item])
    
    outlet = Outlet(company_id=uuid.uuid4(), name="Test Outlet")
    outlet.product_price_overrides[product_id] = Money(amount=150, currency="USD")
    outlet.modifier_price_overrides[modifier_id] = Money(amount=20, currency="USD")
    outlet_repo_mock.get_by_id.return_value = outlet
    
    company_mock = MagicMock(spec=Company)
    company_repo_mock.get_by_id.return_value = company_mock
    
    from domain.entities.catalog import ModifierOption
    modifier_opt = ModifierOption(id=modifier_id, name="Milk", price_adjustment=Money(amount=10, currency="USD"))
    group = ModifierGroup(id=group_id, name="Addons", options=[modifier_opt])
    product = Product(id=product_id, name="Coffee", description="", base_price=Money(amount=100, currency="USD"), category_id=uuid.uuid4(), modifier_groups=[group])
    product_repo_mock.get_by_id.return_value = product
    
    current_dt = datetime.now()
    order = create_order_use_case.execute(cart, DeliveryMethod.PICKUP, current_dt)
    
    # Total should be 150 (product override) + 20 (modifier override) = 170
    assert order.items[0].price.amount == 170
    assert order.total_amount.amount == 170
