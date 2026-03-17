import uuid
from datetime import datetime
from typing import List, Callable, Optional, Any

from ..entities.order import Cart, Order, OrderItem
from ..events import (
    OrderCreatedEvent,
    OrderStatusChangedEvent,
)
from ..exceptions import (
    DeliveryNotAvailableError,
    InsufficientPointsError,
    InvalidModifierError,
    ProductInStopListError,
)
from ..interfaces.repositories import (
    IClientRepository,
    ICompanyRepository,
    IOrderRepository,
    IOutletRepository,
    IProductRepository,
)
from ..services.delivery_service import DeliveryService
from ..services.pricing_service import PricingService
from ..value_objects import Address, DeliveryMethod, OrderStatus


class CreateOrderUseCase:
    def __init__(
        self,
        order_repo: IOrderRepository,
        outlet_repo: IOutletRepository,
        product_repo: IProductRepository,
        client_repo: IClientRepository,
        company_repo: ICompanyRepository,
        event_dispatcher: Callable[[Any], None]
    ):
        self.order_repo = order_repo
        self.outlet_repo = outlet_repo
        self.product_repo = product_repo
        self.client_repo = client_repo
        self.company_repo = company_repo
        self.event_dispatcher = event_dispatcher

    def execute(
        self,
        cart: Cart,
        delivery_method: DeliveryMethod,
        current_dt: datetime,
        delivery_address: Address | None = None,
        spend_points: int = 0
    ) -> Order:
        if cart.is_empty():
            raise ValueError("Cart is empty")

        if cart.client_id is None:
            raise ValueError("Client ID is required for order creation")

        outlet = self.outlet_repo.get_by_id(cart.outlet_id)
        if not outlet:
            raise ValueError("Outlet not found")
            
        company = self.company_repo.get_by_id(outlet.company_id)
        if not company:
            raise ValueError("Company not found")

        # 1. Validate Outlet status
        outlet.validate_can_order(current_dt)

        # 2. Validate Delivery Address
        if delivery_method == DeliveryMethod.DELIVERY:
            if not delivery_address:
                raise ValueError("Delivery address is required for delivery")
            if not DeliveryService.is_address_covered(delivery_address, outlet):
                raise DeliveryNotAvailableError("Address is outside delivery zone")

        # 3. Process items and pricing
        order_items = []
        for cart_item in cart.items:
            # Check assortment
            if not outlet.is_in_assortment(cart_item.product_id):
                raise ProductInStopListError(f"Product {cart_item.product_id} is not in local assortment")

            # Check stop lists
            if not outlet.is_product_available(cart_item.product_id):
                raise ProductInStopListError(f"Product {cart_item.product_id} is unavailable")

            for opts in cart_item.selected_modifiers.values():
                for opt_id in opts:
                    if not outlet.is_modifier_available(opt_id):
                        raise ProductInStopListError(f"Modifier {opt_id} is unavailable")

            product = self.product_repo.get_by_id(cart_item.product_id)
            if not product:
                raise ValueError(f"Product {cart_item.product_id} not found")
                
            # Validate modifiers constraints
            for group in product.modifier_groups:
                selected_for_group = cart_item.selected_modifiers.get(group.id, [])
                if not group.validate_selection(selected_for_group):
                    raise InvalidModifierError(f"Modifier constraints violated for group {group.name}")

            unit_price = PricingService.calculate_order_item_price(product, cart_item.selected_modifiers, outlet=outlet)
            order_items.append(
                OrderItem(
                    product_id=cart_item.product_id,
                    quantity=cart_item.quantity,
                    price=unit_price,
                    selected_modifiers=cart_item.selected_modifiers
                )
            )

        order = Order(
            client_id=cart.client_id,
            outlet_id=cart.outlet_id,
            items=order_items,
            delivery_method=delivery_method,
            delivery_address=delivery_address
        )

        # Calculate raw total early to validate loyalty limit
        order.calculate_total()
        
        if order.total_amount is None:
            raise ValueError("Calculated order total cannot be None")
        
        # 4. Handle loyalty points
        if spend_points > 0 and cart.client_id:
            profile = self.client_repo.get_loyalty_profile(cart.client_id, outlet.company_id)
            if not profile:
                raise InsufficientPointsError("Client has no profile for this company")

            max_discount = PricingService.calculate_max_loyalty_discount(order.total_amount, company)
            if spend_points > max_discount:
                spend_points = max_discount

            profile.spend_points(spend_points)
            self.client_repo.save_loyalty_profile(profile)
            order.applied_loyalty_points = spend_points
            order.calculate_total() # Recalculate physical money total

        self.order_repo.save(order)

        # 5. Dispatch Event
        self.event_dispatcher(
            OrderCreatedEvent(
                occurred_on=current_dt,
                order_id=order.id,
                client_id=order.client_id,
                outlet_id=order.outlet_id,
                total_amount=order.total_amount.amount
            )
        )
        return order


class ChangeOrderStatusUseCase:
    def __init__(
        self,
        order_repo: IOrderRepository,
        event_dispatcher: Callable[[Any], None]
    ):
        self.order_repo = order_repo
        self.event_dispatcher = event_dispatcher

    def execute(self, order_id: uuid.UUID, new_status: OrderStatus, current_dt: datetime) -> Order:
        order = self.order_repo.get_by_id(order_id)
        if not order:
            raise ValueError("Order not found")

        old_status = order.status
        order.change_status(new_status)

        self.order_repo.save(order)

        self.event_dispatcher(
            OrderStatusChangedEvent(
                occurred_on=current_dt,
                order_id=order.id,
                old_status=old_status,
                new_status=new_status
            )
        )
        return order
