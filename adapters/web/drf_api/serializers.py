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
        default=dict
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
    status = serializers.CharField(source='status.value')
    delivery_method = serializers.CharField(source='delivery_method.value')
    total_amount = MoneySerializer(required=False, allow_null=True)

class ChangeOrderStatusRequestSerializer(serializers.Serializer):
    order_id = serializers.UUIDField()
    new_status = serializers.CharField()
