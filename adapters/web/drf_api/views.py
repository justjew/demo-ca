import uuid

from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from config.di import Container
from domain.entities.order import Cart, CartItem
from domain.value_objects import Address, DeliveryMethod, OrderStatus

from .serializers import (
    ChangeOrderStatusRequestSerializer,
    CreateOrderRequestSerializer,
    OrderResponseSerializer,
)


class OrderCreateView(APIView):
    def post(self, request):
        serializer = CreateOrderRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        cart_data = data['cart']

        # Mapping to Domain Entities
        cart_items = [
            CartItem(
                id=uuid.uuid4(),
                product_id=item['product_id'],
                quantity=item['quantity'],
                selected_modifiers=item.get('selected_modifiers', {})
            )
            for item in cart_data['items']
        ]
        cart = Cart(
            id=uuid.uuid4(),
            client_id=cart_data.get('client_id'),
            outlet_id=cart_data['outlet_id'],
            items=cart_items
        )

        delivery_address = None
        if data.get('delivery_address'):
            delivery_address = Address(**data['delivery_address'])

        # Dependency Injection (resolving the use case from the Composition Root)
        use_case = Container.get_create_order_use_case()

        try:
            order = use_case.execute(
                cart=cart,
                delivery_method=DeliveryMethod(data['delivery_method']),
                current_dt=timezone.now(),
                delivery_address=delivery_address,
                spend_points=data.get('spend_points', 0),
                scheduled_time=data.get('scheduled_time')
            )
            response_serializer = OrderResponseSerializer(order)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            # We would normally catch DomainExceptions here and map appropriately,
            # broad catch for demonstration
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class OrderChangeStatusView(APIView):
    def post(self, request):
        serializer = ChangeOrderStatusRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data

        use_case = Container.get_change_order_status_use_case()
        try:
            order = use_case.execute(
                order_id=data['order_id'],
                new_status=OrderStatus(data['new_status']),
                current_dt=timezone.now()
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
                order_id=uuid.UUID(order_id),
                current_dt=timezone.now()
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
            return Response({"detail": "Invalid payload"}, status=status.HTTP_400_BAD_REQUEST)

        use_case = Container.get_manage_stop_list_use_case()
        try:
            if action == "add":
                use_case.add_product_to_stop_list(uuid.UUID(outlet_id), uuid.UUID(product_id_str))
            else:
                use_case.remove_product_from_stop_list(uuid.UUID(outlet_id), uuid.UUID(product_id_str))
            return Response({"status": "Success"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

