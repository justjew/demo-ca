import uuid

from domain.entities.catalog import Category, ModifierGroup, ModifierOption, Product
from domain.entities.client import Client, LoyaltyProfile
from domain.entities.company import Company, LoyaltyLevel
from domain.entities.order import Cart, CartItem, Order
from domain.entities.outlet import Outlet
from domain.value_objects import DeliveryMethod, Money, OrderStatus


def test_happy_path():
    print("Starting Happy Path Test...")
    company = Company(
        id=uuid.uuid4(),
        name="Test Food Group",
        tax_id="12345",
        loyalty_levels=[
            LoyaltyLevel(id=uuid.uuid4(), name="Default", min_spent_amount=0, accrual_rate=0.10)
        ],
    )
    outlet = Outlet(
        id=uuid.uuid4(),
        company_id=company.id,
        name="Test Outlet",
        is_accepting_orders=True,
    )

    category = Category(id=uuid.uuid4(), name="Pizza")

    # 1. Setup Modifiers
    opt1 = ModifierOption(
        id=uuid.uuid4(), name="Extra Cheese", price_adjustment=Money(amount=50)
    )
    opt2 = ModifierOption(
        id=uuid.uuid4(), name="No Onions", price_adjustment=Money(amount=0)
    )
    group = ModifierGroup(
        id=uuid.uuid4(),
        name="Toppings",
        options=[opt1, opt2],
        min_selections=0,
        max_selections=2,
    )

    # 2. Setup Product
    product = Product(
        id=uuid.uuid4(),
        name="Pepperoni",
        description="Classic",
        base_price=Money(amount=500),
        category_id=category.id,
        modifier_groups=[group],
    )

    # 3. Setup Client
    client = Client(id=uuid.uuid4(), phone_number="+1234567890", first_name="John")
    profile = LoyaltyProfile(
        id=uuid.uuid4(), client_id=client.id, company_id=company.id, balance=100
    )

    # 4. Create Cart
    cart_item = CartItem(
        id=uuid.uuid4(),
        product_id=product.id,
        quantity=2,
        selected_modifiers={group.id: [opt1.id]},
    )
    _ = Cart(
        id=uuid.uuid4(), client_id=client.id, outlet_id=outlet.id, items=[cart_item]
    )

    # 5. Use Case Mock execution (manual since we lack concrete repos for now, just validating math & rules)
    from domain.services.pricing_service import PricingService

    unit_price = PricingService.calculate_order_item_price(
        product, cart_item.selected_modifiers
    )
    assert unit_price.amount == 550, f"Expected 550, got {unit_price.amount}"

    from domain.entities.order import OrderItem

    o_item = OrderItem(
        id=uuid.uuid4(),
        product_id=cart_item.product_id,
        quantity=cart_item.quantity,
        price=unit_price,
        selected_modifiers=cart_item.selected_modifiers,
    )

    order = Order(
        id=uuid.uuid4(),
        client_id=client.id,
        outlet_id=outlet.id,
        items=[o_item],
        delivery_method=DeliveryMethod.PICKUP,
    )

    order.calculate_total()
    assert order.total_amount is not None
    assert order.total_amount.amount == 1100, (
        f"Expected 1100, got {order.total_amount.amount}"
    )

    # Apply Loyalty
    max_discount = PricingService.calculate_max_loyalty_discount(
        order.total_amount, company
    )
    assert max_discount == 550, f"Expected 550 max discount, got {max_discount}"

    spend = 100
    if profile.can_spend(spend):
        profile.spend_points(spend)
        order.applied_loyalty_points = spend
        order.calculate_total()

    assert order.total_amount is not None
    assert order.total_amount.amount == 1000, (
        f"Expected 1000, got {order.total_amount.amount}"
    )

    # 6. Test state machine
    order.change_status(OrderStatus.AWAITING_PAYMENT)
    order.change_status(OrderStatus.ACCEPTED)
    order.change_status(OrderStatus.READY)
    order.change_status(OrderStatus.TRANSFERRED)
    order.change_status(OrderStatus.COMPLETED)

    # 7. Accrue points
    from domain.services.loyalty_service import LoyaltyService

    accrued = LoyaltyService.calculate_accrual(
        order.total_amount, company, spent_points=0
    )
    assert accrued == 100, f"Expected 100, got {accrued}"

    print("Happy Path Test Passed!")


if __name__ == "__main__":
    test_happy_path()
