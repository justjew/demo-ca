import uuid
from typing import Any, cast

from django.utils import timezone
from rest_framework import serializers as drf_serializers
from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from config.di import Container
from domain.entities.order import Cart, CartItem
from domain.use_cases.catalog_cases import ProductCreateDTO, ProductUpdateDTO
from domain.use_cases.client_cases import ClientCreateDTO, ClientUpdateDTO
from domain.use_cases.company_cases import (
    CompanyCreateDTO,
    CompanyUpdateDTO,
    LoyaltyLevelDTO,
)
from domain.use_cases.outlet_cases import (
    MoneyDTO,
    OutletCreateDTO,
    OutletUpdateDTO,
    ScheduleDTO,
    WorkingHoursDTO,
)
from domain.value_objects import Address, DeliveryMethod, OrderStatus

from .serializers import (
    ChangeOrderStatusRequestSerializer,
    ClientRequestSerializer,
    ClientResponseSerializer,
    CompanyRequestSerializer,
    CompanyResponseSerializer,
    ConfigureModifiersRequestSerializer,
    CreateOrderRequestSerializer,
    OrderResponseSerializer,
    OutletRequestSerializer,
    OutletResponseSerializer,
    ProductRequestSerializer,
    ProductResponseSerializer,
)

# =====================================================
# Existing non-CRUD views (unchanged)
# =====================================================


class OrderCreateView(APIView):
    def post(self, request):
        serializer = CreateOrderRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = cast(dict[str, Any], serializer.validated_data)
        assert data is not None
        cart_data = data["cart"]

        cart_items = [
            CartItem(
                id=uuid.uuid4(),
                product_id=item["product_id"],
                quantity=item["quantity"],
                selected_modifiers=item.get("selected_modifiers", {}),
            )
            for item in cart_data["items"]
        ]
        cart = Cart(
            id=uuid.uuid4(),
            client_id=cart_data.get("client_id"),
            outlet_id=cart_data["outlet_id"],
            items=cart_items,
        )

        delivery_address = None
        if data.get("delivery_address"):
            delivery_address = Address(**data["delivery_address"])

        use_case = Container.get_create_order_use_case()

        try:
            order = use_case.execute(
                cart=cart,
                delivery_method=DeliveryMethod(data["delivery_method"]),
                current_dt=timezone.now(),
                delivery_address=delivery_address,
                spend_points=data.get("spend_points", 0),
                scheduled_time=data.get("scheduled_time"),
            )
            response_serializer = OrderResponseSerializer(order)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class OrderChangeStatusView(APIView):
    def post(self, request):
        serializer = ChangeOrderStatusRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = cast(dict[str, Any], serializer.validated_data)
        assert data is not None

        use_case = Container.get_change_order_status_use_case()
        try:
            order = use_case.execute(
                order_id=data["order_id"],
                new_status=OrderStatus(data["new_status"]),
                current_dt=timezone.now(),
            )
            response_serializer = OrderResponseSerializer(order)
            return Response(response_serializer.data, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class OrderProcessPaymentView(APIView):
    def post(self, request, order_id):
        use_case = Container.get_process_payment_use_case()
        try:
            order = use_case.execute(
                order_id=uuid.UUID(order_id), current_dt=timezone.now()
            )
            response_serializer = OrderResponseSerializer(order)
            return Response(response_serializer.data, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class CatalogOutletListView(APIView):
    def get(self, request, company_id):
        repo = Container.get_outlet_repo()
        outlets = repo.list_by_company(uuid.UUID(company_id))

        data = [
            {
                "id": str(outlet.id),
                "name": outlet.name,
                "is_accepting_orders": outlet.is_accepting_orders,
            }
            for outlet in outlets
        ]
        return Response(data, status=status.HTTP_200_OK)


class CatalogStopListView(APIView):
    def post(self, request, outlet_id):
        product_id_str = request.data.get("product_id")
        action = request.data.get("action")

        if not product_id_str or action not in ["add", "remove"]:
            return Response(
                {"detail": "Invalid payload"}, status=status.HTTP_400_BAD_REQUEST
            )

        use_case = Container.get_manage_stop_list_use_case()
        try:
            if action == "add":
                use_case.add_product_to_stop_list(
                    uuid.UUID(outlet_id), uuid.UUID(product_id_str)
                )
            else:
                use_case.remove_product_from_stop_list(
                    uuid.UUID(outlet_id), uuid.UUID(product_id_str)
                )
            return Response({"status": "Success"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class CatalogConfigureModifiersView(APIView):
    def post(self, request, product_id):
        serializer = ConfigureModifiersRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = cast(dict[str, Any], serializer.validated_data)
        assert data is not None
        group_data = data["group"]

        from domain.entities.catalog import ModifierGroup, ModifierOption
        from domain.value_objects import Money

        options = [
            ModifierOption(
                id=opt["id"],
                name=opt["name"],
                price_adjustment=Money(
                    amount=opt["price_amount"], currency=opt["price_currency"]
                ),
                is_available=opt["is_available"],
            )
            for opt in group_data["options"]
        ]

        group = ModifierGroup(
            id=group_data["id"],
            name=group_data["name"],
            options=options,
            is_required=group_data["is_required"],
            min_selections=group_data["min_selections"],
            max_selections=group_data["max_selections"],
        )

        use_case = Container.get_configure_modifiers_use_case()
        try:
            use_case.add_modifier_group(uuid.UUID(product_id), group)
            return Response({"status": "Success"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ExternalOrderAcceptView(APIView):
    def post(self, request):
        use_case = Container.get_accept_external_order_use_case()
        try:
            order = use_case.execute(payload=request.data, current_dt=timezone.now())
            response_serializer = OrderResponseSerializer(order)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class LoyaltyCalculateAccrualView(APIView):
    def post(self, request, order_id):
        use_case = Container.get_calculate_accrual_use_case()
        try:
            use_case.execute(order_id=uuid.UUID(order_id), current_dt=timezone.now())
            return Response({"status": "Success"}, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)


# =====================================================
# Generic CRUD ViewSet
# =====================================================


class CrudViewSet(viewsets.ViewSet):
    """
    Generic ViewSet that delegates all CRUD work to a CrudUseCase.

    Subclasses configure via class attributes:
      - request_serializer_class
      - response_serializer_class
      - create_dto_class / update_dto_class
      - get_use_case()   — must return a CrudUseCase instance

    For entities that need custom DTO building from validated data,
    override `build_create_dto(data)` or `build_update_dto(data)`.
    """

    request_serializer_class: type[drf_serializers.Serializer]
    response_serializer_class: type[drf_serializers.Serializer]
    create_dto_class: type
    update_dto_class: type

    @classmethod
    def get_use_case(cls):
        raise NotImplementedError

    def build_create_dto(self, validated_data: dict) -> Any:
        return self.create_dto_class(**validated_data)

    def build_update_dto(self, validated_data: dict) -> Any:
        return self.update_dto_class(**validated_data)

    def create(self, request):
        serializer = self.request_serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        dto = self.build_create_dto(serializer.validated_data)
        entity = self.get_use_case().create(dto)
        return Response(
            self.response_serializer_class(entity).data,
            status=status.HTTP_201_CREATED,
        )

    def retrieve(self, request, pk=None):
        entity = self.get_use_case().get(uuid.UUID(pk))
        if not entity:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return Response(self.response_serializer_class(entity).data)

    def update(self, request, pk=None):
        serializer = self.request_serializer_class(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        dto = self.build_update_dto(serializer.validated_data)
        try:
            entity = self.get_use_case().update(uuid.UUID(pk), dto)
            return Response(self.response_serializer_class(entity).data)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)

    def destroy(self, request, pk=None):
        self.get_use_case().delete(uuid.UUID(pk))
        return Response(status=status.HTTP_204_NO_CONTENT)

    def list(self, request):
        try:
            limit = int(request.query_params.get("limit", 10))
            offset = int(request.query_params.get("offset", 0))
        except ValueError:
            limit, offset = 10, 0
        entities = self.get_use_case().list(limit=limit, offset=offset)
        return Response(self.response_serializer_class(entities, many=True).data)


# =====================================================
# Concrete ViewSets (declarative, minimal code)
# =====================================================


class ClientViewSet(CrudViewSet):
    request_serializer_class = ClientRequestSerializer
    response_serializer_class = ClientResponseSerializer
    create_dto_class = ClientCreateDTO
    update_dto_class = ClientUpdateDTO

    @classmethod
    def get_use_case(cls):
        return Container.get_client_crud()


class CompanyViewSet(CrudViewSet):
    request_serializer_class = CompanyRequestSerializer
    response_serializer_class = CompanyResponseSerializer
    create_dto_class = CompanyCreateDTO
    update_dto_class = CompanyUpdateDTO

    @classmethod
    def get_use_case(cls):
        return Container.get_company_crud()

    def build_create_dto(self, validated_data: dict) -> CompanyCreateDTO:
        levels_dto = None
        if "loyalty_levels" in validated_data:
            levels_dto = [
                LoyaltyLevelDTO(**lvl) for lvl in validated_data["loyalty_levels"]
            ]
        return CompanyCreateDTO(
            name=validated_data["name"],
            tax_id=validated_data["tax_id"],
            loyalty_levels=levels_dto,
            max_loyalty_payment_percent=validated_data.get(
                "max_loyalty_payment_percent", 0.50
            ),
        )

    def build_update_dto(self, validated_data: dict) -> CompanyUpdateDTO:
        levels_dto = None
        if "loyalty_levels" in validated_data:
            levels_dto = [
                LoyaltyLevelDTO(**lvl) for lvl in validated_data["loyalty_levels"]
            ]
        return CompanyUpdateDTO(
            name=validated_data.get("name"),
            tax_id=validated_data.get("tax_id"),
            loyalty_levels=levels_dto,
            max_loyalty_payment_percent=validated_data.get(
                "max_loyalty_payment_percent"
            ),
        )


class OutletViewSet(CrudViewSet):
    request_serializer_class = OutletRequestSerializer
    response_serializer_class = OutletResponseSerializer
    create_dto_class = OutletCreateDTO
    update_dto_class = OutletUpdateDTO

    @classmethod
    def get_use_case(cls):
        return Container.get_outlet_crud()

    @staticmethod
    def _parse_schedule(schedule_data):
        if not schedule_data:
            return None
        kwargs = {}
        for day in [
            "monday",
            "tuesday",
            "wednesday",
            "thursday",
            "friday",
            "saturday",
            "sunday",
        ]:
            if day in schedule_data and schedule_data[day]:
                kwargs[day] = WorkingHoursDTO(
                    open_time=str(schedule_data[day]["open_time"]),
                    close_time=str(schedule_data[day]["close_time"]),
                )
        return ScheduleDTO(**kwargs)

    @staticmethod
    def _parse_overrides(overrides_data):
        if not overrides_data:
            return None
        return {
            uuid.UUID(k): MoneyDTO(amount=v["amount"], currency=v["currency"])
            for k, v in overrides_data.items()
        }

    def build_create_dto(self, validated_data: dict) -> OutletCreateDTO:
        return OutletCreateDTO(
            company_id=validated_data["company_id"],
            name=validated_data["name"],
            is_accepting_orders=validated_data.get("is_accepting_orders", True),
            schedule=self._parse_schedule(validated_data.get("schedule")),
        )

    def build_update_dto(self, validated_data: dict) -> OutletUpdateDTO:
        return OutletUpdateDTO(
            name=validated_data.get("name"),
            is_accepting_orders=validated_data.get("is_accepting_orders"),
            schedule=self._parse_schedule(validated_data.get("schedule"))
            if "schedule" in validated_data
            else None,
            product_price_overrides=self._parse_overrides(
                validated_data.get("product_price_overrides")
            ),
            modifier_price_overrides=self._parse_overrides(
                validated_data.get("modifier_price_overrides")
            ),
        )


class ProductViewSet(CrudViewSet):
    request_serializer_class = ProductRequestSerializer
    response_serializer_class = ProductResponseSerializer
    create_dto_class = ProductCreateDTO
    update_dto_class = ProductUpdateDTO

    @classmethod
    def get_use_case(cls):
        return Container.get_product_crud()
