import uuid
from datetime import time
from typing import Any, cast

from domain.entities.catalog import ModifierGroup, ModifierOption, Product
from domain.entities.client import Client, LoyaltyProfile
from domain.entities.company import Company, LoyaltyLevel
from domain.entities.order import Order, OrderItem
from domain.entities.outlet import Outlet
from domain.interfaces.repositories import (
    IClientRepository,
    ICompanyRepository,
    IOrderRepository,
    IOutletRepository,
    IProductRepository,
)
from domain.value_objects import (
    Address,
    DeliveryMethod,
    Money,
    OrderStatus,
    Schedule,
    WorkingHours,
)

from .models import (
    ClientModel,
    CompanyModel,
    LoyaltyProfileModel,
    OrderItemModel,
    OrderModel,
    OutletModel,
    ProductModel,
)


class DjangoCompanyRepository(ICompanyRepository):
    def get_by_id(self, company_id: uuid.UUID) -> Company | None:
        try:
            model = CompanyModel.objects.get(id=company_id)
            levels = [
                LoyaltyLevel(id=uuid.uuid4(), **lvl)
                for lvl in cast(list[dict[str, Any]], model.loyalty_levels_data)
            ]
            return Company(
                id=cast(uuid.UUID, model.id),
                name=str(model.name),
                tax_id=str(model.tax_id),
                loyalty_levels=levels,
                max_loyalty_payment_percent=float(model.max_loyalty_payment_percent),
            )
        except CompanyModel.DoesNotExist:
            return None

    def save(self, company: Company) -> None:
        levels_data = [
            {
                "name": lvl.name,
                "min_spent_amount": lvl.min_spent_amount,
                "accrual_rate": lvl.accrual_rate,
            }
            for lvl in company.loyalty_levels
        ]
        CompanyModel.objects.update_or_create(
            id=company.id,
            defaults={
                "name": company.name,
                "tax_id": company.tax_id,
                "loyalty_levels_data": levels_data,
                "max_loyalty_payment_percent": company.max_loyalty_payment_percent,
            },
        )


class DjangoOutletRepository(IOutletRepository):
    def get_by_id(self, outlet_id: uuid.UUID) -> Outlet | None:
        try:
            model = OutletModel.objects.get(id=outlet_id)
            return self._to_entity(model)
        except OutletModel.DoesNotExist:
            return None

    def list_by_company(self, company_id: uuid.UUID) -> list[Outlet]:
        models = OutletModel.objects.filter(company_id=company_id)
        return [self._to_entity(model) for model in models]

    def save(self, outlet: Outlet) -> None:
        # Save schedule details if present
        schedule_data = None
        if outlet.schedule:
            schedule_data = {}
            for day in [
                "monday",
                "tuesday",
                "wednesday",
                "thursday",
                "friday",
                "saturday",
                "sunday",
            ]:
                wh = getattr(outlet.schedule, day)
                if wh:
                    schedule_data[day] = {
                        "open_time": wh.open_time.isoformat(),
                        "close_time": wh.close_time.isoformat(),
                    }

        product_price_overrides = {
            str(k): {"amount": v.amount, "currency": v.currency}
            for k, v in outlet.product_price_overrides.items()
        }
        modifier_price_overrides = {
            str(k): {"amount": v.amount, "currency": v.currency}
            for k, v in outlet.modifier_price_overrides.items()
        }

        OutletModel.objects.update_or_create(
            id=outlet.id,
            defaults={
                "company_id": outlet.company_id,
                "name": outlet.name,
                "is_accepting_orders": outlet.is_accepting_orders,
                "schedule_data": schedule_data,
                "product_stop_list": [str(uid) for uid in outlet.product_stop_list],
                "modifier_stop_list": [str(uid) for uid in outlet.modifier_stop_list],
                "local_assortment": [str(uid) for uid in outlet.local_assortment]
                if outlet.local_assortment is not None
                else None,
                "product_price_overrides": product_price_overrides,
                "modifier_price_overrides": modifier_price_overrides,
            },
        )

    def _to_entity(self, model: OutletModel) -> Outlet:
        schedule = None
        if model.schedule_data:
            kwargs = {}
            for day, times in cast(dict[str, Any], model.schedule_data).items():
                kwargs[day] = WorkingHours(
                    open_time=time.fromisoformat(times["open_time"]),
                    close_time=time.fromisoformat(times["close_time"]),
                )
            schedule = Schedule(**kwargs)

        # Deserialize overrides
        product_price_overrides = (
            {
                uuid.UUID(k): Money(**v)
                for k, v in cast(dict[str, Any], model.product_price_overrides).items()
            }
            if model.product_price_overrides
            else {}
        )

        modifier_price_overrides = (
            {
                uuid.UUID(k): Money(**v)
                for k, v in cast(dict[str, Any], model.modifier_price_overrides).items()
            }
            if model.modifier_price_overrides
            else {}
        )

        return Outlet(
            id=cast(uuid.UUID, model.id),
            company_id=cast(
                uuid.UUID, model.company_id if model.company_id else uuid.UUID(int=0)
            ),
            name=str(model.name),
            is_accepting_orders=bool(model.is_accepting_orders),
            schedule=schedule,
            product_stop_list={
                uuid.UUID(uid) for uid in cast(list[str], model.product_stop_list)
            },
            modifier_stop_list={
                uuid.UUID(uid) for uid in cast(list[str], model.modifier_stop_list)
            },
            local_assortment={
                uuid.UUID(uid) for uid in cast(list[str], model.local_assortment)
            }
            if model.local_assortment is not None
            else None,
            product_price_overrides=product_price_overrides,
            modifier_price_overrides=modifier_price_overrides,
        )


class DjangoProductRepository(IProductRepository):
    def get_by_id(self, product_id: uuid.UUID) -> Product | None:
        try:
            model = ProductModel.objects.get(id=product_id)
            return self._to_entity(model)
        except ProductModel.DoesNotExist:
            return None

    def get_many(self, product_ids: list[uuid.UUID]) -> list[Product]:
        models = ProductModel.objects.filter(id__in=product_ids)
        return [self._to_entity(model) for model in models]

    def save(self, product: Product) -> None:
        # Convert modifier groups to dict list
        groups_data = []
        for group in product.modifier_groups:
            opts_data = [
                {
                    "id": str(opt.id),
                    "name": opt.name,
                    "price_amount": opt.price_adjustment.amount,
                    "price_currency": opt.price_adjustment.currency,
                    "is_available": opt.is_available,
                }
                for opt in group.options
            ]
            groups_data.append(
                {
                    "id": str(group.id),
                    "name": group.name,
                    "options": opts_data,
                    "is_required": group.is_required,
                    "min_selections": group.min_selections,
                    "max_selections": group.max_selections,
                }
            )

        ProductModel.objects.update_or_create(
            id=product.id,
            defaults={
                "name": product.name,
                "description": product.description,
                "base_price_amount": product.base_price.amount,
                "base_price_currency": product.base_price.currency,
                "category_id": product.category_id,
                "modifier_groups_data": groups_data,
                "is_active": product.is_active,
            },
        )

    def _to_entity(self, model: ProductModel) -> Product:
        groups = []
        for g_data in cast(list[dict[str, Any]], model.modifier_groups_data):
            options = [
                ModifierOption(
                    id=uuid.UUID(opt["id"]),
                    name=opt["name"],
                    price_adjustment=Money(
                        amount=opt["price_amount"], currency=opt["price_currency"]
                    ),
                    is_available=opt.get("is_available", True),
                )
                for opt in g_data.get("options", [])
            ]
            groups.append(
                ModifierGroup(
                    id=uuid.UUID(g_data["id"]),
                    name=g_data["name"],
                    options=options,
                    is_required=g_data.get("is_required", False),
                    min_selections=g_data.get("min_selections", 0),
                    max_selections=g_data.get("max_selections", 1),
                )
            )

        return Product(
            id=cast(uuid.UUID, model.id),
            name=str(model.name),
            description=str(model.description),
            base_price=Money(
                amount=cast(int, model.base_price_amount),
                currency=str(model.base_price_currency),
            ),
            category_id=cast(uuid.UUID, model.category_id if model.category_id else None),
            modifier_groups=groups,
            is_active=bool(model.is_active),
        )


class DjangoClientRepository(IClientRepository):
    def get_by_phone(self, phone: str) -> Client | None:
        try:
            model = ClientModel.objects.get(phone_number=phone)
            return Client(
                id=cast(uuid.UUID, model.id),
                phone_number=str(model.phone_number),
                first_name=str(model.first_name) if model.first_name else None,
                last_name=str(model.last_name) if model.last_name else None,
            )
        except ClientModel.DoesNotExist:
            return None

    def get_loyalty_profile(
        self, client_id: uuid.UUID, company_id: uuid.UUID
    ) -> LoyaltyProfile | None:
        try:
            model = LoyaltyProfileModel.objects.get(
                client_id=client_id, company_id=company_id
            )
            return LoyaltyProfile(
                id=cast(uuid.UUID, model.id),
                client_id=cast(uuid.UUID, model.client.id),
                company_id=cast(uuid.UUID, model.company.id),
                balance=int(model.balance),
                total_spent=int(model.total_spent),
            )
        except LoyaltyProfileModel.DoesNotExist:
            return None

    def save_loyalty_profile(self, profile: LoyaltyProfile) -> None:
        LoyaltyProfileModel.objects.update_or_create(
            client_id=profile.client_id,
            company_id=profile.company_id,
            defaults={
                "id": profile.id,
                "balance": profile.balance,
                "total_spent": profile.total_spent,
            },
        )

    def save_client(self, client: Client) -> None:
        # Useful helper for future
        ClientModel.objects.update_or_create(
            id=client.id,
            defaults={
                "phone_number": client.phone_number,
                "first_name": client.first_name,
                "last_name": client.last_name,
            },
        )


class DjangoOrderRepository(IOrderRepository):
    def get_by_id(self, order_id: uuid.UUID) -> Order | None:
        try:
            model = OrderModel.objects.prefetch_related("items").get(id=order_id)

            delivery_address = None
            if model.delivery_address_data:
                delivery_address = Address(
                    **cast(dict[str, Any], model.delivery_address_data)
                )

            items = []
            for item_model in model.items.all():
                selected_mods = {
                    uuid.UUID(k): [uuid.UUID(uid) for uid in v]
                    for k, v in cast(
                        dict[str, list[str]], item_model.selected_modifiers_data
                    ).items()
                }
                items.append(
                    OrderItem(
                        id=cast(uuid.UUID, item_model.id),
                        product_id=cast(uuid.UUID, item_model.product_id),
                        quantity=int(item_model.quantity),
                        price=Money(
                            amount=int(item_model.price_amount),
                            currency=str(item_model.price_currency),
                        ),
                        selected_modifiers=selected_mods,
                    )
                )

            total_amount = None
            if (
                model.total_amount_amount is not None
                and model.total_amount_currency is not None
            ):
                total_amount = Money(
                    amount=model.total_amount_amount,
                    currency=model.total_amount_currency,
                )

            return Order(
                id=cast(uuid.UUID, model.id),
                client_id=cast(uuid.UUID, model.client.id) if model.client else None,
                outlet_id=cast(uuid.UUID, model.outlet.id),
                items=items,
                delivery_method=DeliveryMethod(str(model.delivery_method)),
                status=OrderStatus(str(model.status)),
                delivery_address=delivery_address,
                scheduled_time=model.scheduled_time,
                applied_loyalty_points=int(model.applied_loyalty_points),
                total_amount=total_amount,
                receipt_id=str(model.receipt_id) if model.receipt_id else None,
                delivery_tracking_id=str(model.delivery_tracking_id)
                if model.delivery_tracking_id
                else None,
                external_id=str(model.external_id) if model.external_id else None,
            )
        except OrderModel.DoesNotExist:
            return None

    def save(self, order: Order) -> None:
        address_data = None
        if order.delivery_address:
            address_data = {
                "city": order.delivery_address.city,
                "street": order.delivery_address.street,
                "building": order.delivery_address.building,
                "apartment": order.delivery_address.apartment,
                "latitude": order.delivery_address.latitude,
                "longitude": order.delivery_address.longitude,
            }

        total_amount = None
        total_currency = None
        if order.total_amount:
            total_amount = order.total_amount.amount
            total_currency = order.total_amount.currency

        order_model, _ = OrderModel.objects.update_or_create(
            id=order.id,
            defaults={
                "client_id": order.client_id,
                "outlet_id": order.outlet_id,
                "delivery_method": order.delivery_method.value,
                "status": order.status.value,
                "delivery_address_data": address_data,
                "scheduled_time": order.scheduled_time,
                "applied_loyalty_points": order.applied_loyalty_points,
                "total_amount_amount": total_amount,
                "total_amount_currency": total_currency,
                "receipt_id": order.receipt_id,
                "delivery_tracking_id": order.delivery_tracking_id,
                "external_id": order.external_id,
            },
        )

        # Sync items (simple approach: clear and recreate if not too many)
        # Note: If order is created once, this works fine.
        order_model.items.all().delete()
        for item in order.items:
            selected_mods_data = {
                str(k): [str(uid) for uid in v]
                for k, v in item.selected_modifiers.items()
            }
            OrderItemModel.objects.create(
                id=item.id,
                order=order_model,
                product_id=item.product_id,
                quantity=item.quantity,
                price_amount=item.price.amount,
                price_currency=item.price.currency,
                selected_modifiers_data=selected_mods_data,
            )
