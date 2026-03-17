import uuid

from django.db import models


class CompanyModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    tax_id = models.CharField(max_length=50)
    loyalty_levels_data = models.JSONField(default=list, blank=True)
    max_loyalty_payment_percent = models.FloatField(default=0.50)

    def __str__(self):
        return self.name

class OutletModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(CompanyModel, on_delete=models.CASCADE, related_name="outlets")
    name = models.CharField(max_length=255)
    is_accepting_orders = models.BooleanField(default=True)
    schedule_data = models.JSONField(null=True, blank=True)

    product_stop_list = models.JSONField(default=list, blank=True)
    modifier_stop_list = models.JSONField(default=list, blank=True)
    local_assortment = models.JSONField(null=True, blank=True)
    product_price_overrides = models.JSONField(default=dict, blank=True)
    modifier_price_overrides = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return self.name

class CategoryModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class ProductModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    category = models.ForeignKey(CategoryModel, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    base_price_amount = models.IntegerField()
    base_price_currency = models.CharField(max_length=3, default="RUB")
    modifier_groups_data = models.JSONField(default=list, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class ClientModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    phone_number = models.CharField(max_length=20, unique=True)
    first_name = models.CharField(max_length=100, null=True, blank=True)
    last_name = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return self.phone_number

class LoyaltyProfileModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client = models.ForeignKey(ClientModel, on_delete=models.CASCADE, related_name="loyalty_profiles")
    company = models.ForeignKey(CompanyModel, on_delete=models.CASCADE)
    balance = models.IntegerField(default=0)
    total_spent = models.IntegerField(default=0)

    class Meta:
        unique_together = ('client', 'company')

class OrderModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client = models.ForeignKey(ClientModel, on_delete=models.SET_NULL, null=True, blank=True, related_name="orders")
    outlet = models.ForeignKey(OutletModel, on_delete=models.PROTECT)
    delivery_method = models.CharField(max_length=50)
    status = models.CharField(max_length=50)

    delivery_address_data = models.JSONField(null=True, blank=True)
    scheduled_time = models.DateTimeField(null=True, blank=True)
    applied_loyalty_points = models.IntegerField(default=0)

    total_amount_amount = models.IntegerField(null=True, blank=True)
    total_amount_currency = models.CharField(max_length=3, null=True, blank=True)

    receipt_id = models.CharField(max_length=100, null=True, blank=True)
    delivery_tracking_id = models.CharField(max_length=100, null=True, blank=True)
    external_id = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return f"Order {self.id}"

class OrderItemModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(OrderModel, on_delete=models.CASCADE, related_name="items")
    product_id = models.UUIDField()
    quantity = models.IntegerField()
    price_amount = models.IntegerField()
    price_currency = models.CharField(max_length=3, default="RUB")
    selected_modifiers_data = models.JSONField(default=dict, blank=True)
