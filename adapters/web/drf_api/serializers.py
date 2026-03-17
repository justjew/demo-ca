from rest_framework import serializers


class AddressSerializer(serializers.Serializer):
    city = serializers.CharField()
    street = serializers.CharField()
    building = serializers.CharField()
    apartment = serializers.CharField(required=False, allow_null=True)
    latitude = serializers.FloatField(required=False, allow_null=True)
    longitude = serializers.FloatField(required=False, allow_null=True)


class CartItemSerializer(serializers.Serializer):
    product_id = serializers.UUIDField()
    quantity = serializers.IntegerField(min_value=1)
    selected_modifiers = serializers.DictField(
        child=serializers.ListField(child=serializers.UUIDField()),
        required=False,
        default=dict,
    )


class CartSerializer(serializers.Serializer):
    client_id = serializers.UUIDField(required=False, allow_null=True)
    outlet_id = serializers.UUIDField()
    items = CartItemSerializer(many=True)


class CreateOrderRequestSerializer(serializers.Serializer):
    cart = CartSerializer()
    delivery_method = serializers.ChoiceField(choices=["PICKUP", "DELIVERY"])
    delivery_address = AddressSerializer(required=False, allow_null=True)
    spend_points = serializers.IntegerField(min_value=0, default=0)
    scheduled_time = serializers.DateTimeField(required=False, allow_null=True)


class MoneySerializer(serializers.Serializer):
    amount = serializers.IntegerField()
    currency = serializers.CharField()


class OrderItemResponseSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    product_id = serializers.UUIDField()
    quantity = serializers.IntegerField()
    price = MoneySerializer()


class OrderResponseSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    client_id = serializers.UUIDField(required=False, allow_null=True)
    outlet_id = serializers.UUIDField()
    status = serializers.CharField(source="status.value")
    delivery_method = serializers.CharField(source="delivery_method.value")
    total_amount = MoneySerializer(required=False, allow_null=True)


class ChangeOrderStatusRequestSerializer(serializers.Serializer):
    order_id = serializers.UUIDField()
    new_status = serializers.CharField()


class ModifierOptionSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    name = serializers.CharField()
    price_amount = serializers.IntegerField()
    price_currency = serializers.CharField(default="RUB")
    is_available = serializers.BooleanField(default=True)


class ModifierGroupSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    name = serializers.CharField()
    options = ModifierOptionSerializer(many=True)
    is_required = serializers.BooleanField(default=False)
    min_selections = serializers.IntegerField(default=0)
    max_selections = serializers.IntegerField(default=1)


class ConfigureModifiersRequestSerializer(serializers.Serializer):
    group = ModifierGroupSerializer()


# -----------------------------------------------------
# CRUD API Serializers
# -----------------------------------------------------


# Client
class ClientRequestSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=50)
    first_name = serializers.CharField(
        max_length=100, required=False, allow_null=True, allow_blank=True
    )
    last_name = serializers.CharField(
        max_length=100, required=False, allow_null=True, allow_blank=True
    )


class ClientResponseSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    phone_number = serializers.CharField()
    first_name = serializers.CharField(allow_null=True)
    last_name = serializers.CharField(allow_null=True)


# Company
class LoyaltyLevelSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100)
    min_spent_amount = serializers.IntegerField(min_value=0)
    accrual_rate = serializers.FloatField(min_value=0.0)


class CompanyRequestSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    tax_id = serializers.CharField(max_length=50)
    loyalty_levels = LoyaltyLevelSerializer(many=True, required=False)
    max_loyalty_payment_percent = serializers.FloatField(
        min_value=0.0, max_value=1.0, default=0.50
    )


class CompanyResponseSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    name = serializers.CharField()
    tax_id = serializers.CharField()
    # Exposing loyalty_levels back isn't strictly necessary for a brief view, but keeping it symmetric:
    loyalty_levels = serializers.SerializerMethodField()
    max_loyalty_payment_percent = serializers.FloatField()

    def get_loyalty_levels(self, obj):
        # Depending on how the Entity exposes it
        return [
            {
                "name": lvl.name,
                "min_spent_amount": lvl.min_spent_amount,
                "accrual_rate": lvl.accrual_rate,
            }
            for lvl in getattr(obj, "loyalty_levels", [])
        ]


# Outlet
class WorkingHoursSerializer(serializers.Serializer):
    open_time = serializers.TimeField()
    close_time = serializers.TimeField()


class ScheduleSerializer(serializers.Serializer):
    monday = WorkingHoursSerializer(required=False, allow_null=True)
    tuesday = WorkingHoursSerializer(required=False, allow_null=True)
    wednesday = WorkingHoursSerializer(required=False, allow_null=True)
    thursday = WorkingHoursSerializer(required=False, allow_null=True)
    friday = WorkingHoursSerializer(required=False, allow_null=True)
    saturday = WorkingHoursSerializer(required=False, allow_null=True)
    sunday = WorkingHoursSerializer(required=False, allow_null=True)


class OutletRequestSerializer(serializers.Serializer):
    company_id = serializers.UUIDField()
    name = serializers.CharField(max_length=255)
    is_accepting_orders = serializers.BooleanField(default=True)
    schedule = ScheduleSerializer(required=False, allow_null=True)
    product_price_overrides = serializers.DictField(
        child=MoneySerializer(), required=False
    )
    modifier_price_overrides = serializers.DictField(
        child=MoneySerializer(), required=False
    )


class OutletResponseSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    company_id = serializers.UUIDField()
    name = serializers.CharField()
    is_accepting_orders = serializers.BooleanField()
    # Complex fields omitted for brevity if needed, but we can return schedule as dict
    schedule = serializers.SerializerMethodField()

    def get_schedule(self, obj):
        if not obj.schedule:
            return None
        res = {}
        for day in [
            "monday",
            "tuesday",
            "wednesday",
            "thursday",
            "friday",
            "saturday",
            "sunday",
        ]:
            wh = getattr(obj.schedule, day, None)
            if wh:
                res[day] = {"open_time": wh.open_time, "close_time": wh.close_time}
        return res


# Product
class ProductRequestSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    description = serializers.CharField(allow_blank=True)
    base_price_amount = serializers.IntegerField(min_value=0)
    base_price_currency = serializers.CharField(max_length=3, default="RUB")
    category_id = serializers.UUIDField()
    is_active = serializers.BooleanField(default=True)


class ProductResponseSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    name = serializers.CharField()
    description = serializers.CharField()
    base_price = MoneySerializer()
    category_id = serializers.UUIDField()
    is_active = serializers.BooleanField()
