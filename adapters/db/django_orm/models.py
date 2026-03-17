import uuid

from django.db import models


class CompanyModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    objects: models.Manager  # type: ignore
    DoesNotExist: type[Exception]  # type: ignore
    name = models.CharField(max_length=255)
    tax_id = models.CharField(max_length=50)
    loyalty_levels_data = models.JSONField(default=list, blank=True)
    max_loyalty_payment_percent = models.FloatField(default=0.50)  # type: ignore

    def __str__(self) -> str:
        return str(self.name)


class OutletModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    objects: models.Manager  # type: ignore
    DoesNotExist: type[Exception]  # type: ignore
    company = models.ForeignKey(
        CompanyModel, on_delete=models.CASCADE, related_name="outlets"
    )
    company_id: uuid.UUID  # type: ignore
    name = models.CharField(max_length=255)
    is_accepting_orders = models.BooleanField(default=True)  # type: ignore
    schedule_data = models.JSONField(null=True, blank=True)

    product_stop_list = models.JSONField(default=list, blank=True)
    modifier_stop_list = models.JSONField(default=list, blank=True)
    local_assortment = models.JSONField(null=True, blank=True)
    product_price_overrides = models.JSONField(default=dict, blank=True)
    modifier_price_overrides = models.JSONField(default=dict, blank=True)

    def __str__(self) -> str:
        return str(self.name)


class CategoryModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    objects: models.Manager  # type: ignore
    DoesNotExist: type[Exception]  # type: ignore
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)  # type: ignore

    def __str__(self) -> str:
        return str(self.name)


class ProductModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    objects: models.Manager  # type: ignore
    DoesNotExist: type[Exception]  # type: ignore
    category = models.ForeignKey(
        CategoryModel, on_delete=models.SET_NULL, null=True, blank=True
    )
    category_id: uuid.UUID | None  # type: ignore
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    base_price_amount = models.IntegerField()
    base_price_currency = models.CharField(max_length=3, default="RUB")  # type: ignore
    modifier_groups_data = models.JSONField(default=list, blank=True)
    is_active = models.BooleanField(default=True)  # type: ignore

    def __str__(self) -> str:
        return str(self.name)


class ClientModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    objects: models.Manager  # type: ignore
    DoesNotExist: type[Exception]  # type: ignore
    phone_number = models.CharField(max_length=20, unique=True)
    first_name = models.CharField(max_length=100, null=True, blank=True)
    last_name = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self) -> str:
        return str(self.phone_number)


class LoyaltyProfileModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    objects: models.Manager  # type: ignore
    DoesNotExist: type[Exception]  # type: ignore
    client = models.ForeignKey(
        ClientModel, on_delete=models.CASCADE, related_name="loyalty_profiles"
    )
    client_id: uuid.UUID  # type: ignore
    company = models.ForeignKey(CompanyModel, on_delete=models.CASCADE)
    company_id: uuid.UUID  # type: ignore
    balance = models.IntegerField(default=0)  # type: ignore
    total_spent = models.IntegerField(default=0)  # type: ignore

    class Meta:
        unique_together = ("client", "company")


class OrderModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    objects: models.Manager  # type: ignore
    DoesNotExist: type[Exception]  # type: ignore
    client = models.ForeignKey(
        ClientModel,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
    )
    client_id: uuid.UUID | None  # type: ignore
    outlet = models.ForeignKey(OutletModel, on_delete=models.PROTECT)
    outlet_id: uuid.UUID  # type: ignore
    delivery_method = models.CharField(max_length=50)
    status = models.CharField(max_length=50)

    delivery_address_data = models.JSONField(null=True, blank=True)
    scheduled_time = models.DateTimeField(null=True, blank=True)
    applied_loyalty_points = models.IntegerField(default=0)  # type: ignore

    total_amount_amount = models.IntegerField(null=True, blank=True)
    total_amount_currency = models.CharField(max_length=3, null=True, blank=True)

    receipt_id = models.CharField(max_length=100, null=True, blank=True)
    delivery_tracking_id = models.CharField(max_length=100, null=True, blank=True)
    external_id = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self) -> str:
        return f"Order {self.id}"


class OrderItemModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    objects: models.Manager  # type: ignore
    DoesNotExist: type[Exception]  # type: ignore
    order = models.ForeignKey(
        OrderModel, on_delete=models.CASCADE, related_name="items"
    )
    order_id: uuid.UUID  # type: ignore
    product_id = models.UUIDField()
    quantity = models.IntegerField()
    price_amount = models.IntegerField()
    price_currency = models.CharField(max_length=3, default="RUB")
    selected_modifiers_data = models.JSONField(default=dict, blank=True)
