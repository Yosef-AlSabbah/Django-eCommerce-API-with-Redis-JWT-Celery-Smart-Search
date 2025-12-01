from drf_spectacular.utils import extend_schema, OpenApiResponse, extend_schema_view
from rest_framework import viewsets, status
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response

from .models import Order
from .permissions import IsAdminOrOwner
from .serializers import OrderSerializer, OrderCreateSerializer
from .tasks import send_order_confirmation_email


@extend_schema_view(
    list=extend_schema(
        operation_id="order_list",
        description="List orders. Non-staff users see only their orders.",
        tags=["Orders"],
    ),
    retrieve=extend_schema(
        operation_id="order_retrieve",
        description="Retrieve an order by its ID.",
        tags=["Orders"],
    ),
    create=extend_schema(
        operation_id="order_create",
        description="Create an order from the user's cart.",
        tags=["Orders"],
        responses={
            201: OpenApiResponse(response=OrderSerializer, description="Order created successfully."),
            400: OpenApiResponse(description="Bad request (e.g., empty cart, invalid address or coupon)."),
        },
    ),
    # Staff-only actions
    update=extend_schema(operation_id="order_update", description="Update an order. Admin access required.", tags=["Orders"]),
    partial_update=extend_schema(operation_id="order_partial_update", description="Partially update an order. Admin access required.", tags=["Orders"]),
    destroy=extend_schema(operation_id="order_destroy", description="Delete an order. Admin access required.", tags=["Orders"]),
)
class OrderViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing orders.
    - Users can create, list, and retrieve their own orders.
    - Staff users have full CRUD permissions.
    """
    queryset = Order.objects.prefetch_related('items__product', 'user', 'address', 'coupon')

    def get_serializer_class(self):
        """
        Return the appropriate serializer class based on the action.
        """
        if self.action == 'create':
            return OrderCreateSerializer
        return OrderSerializer

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        - 'create', 'list', 'retrieve': Must be authenticated and either owner or admin.
        - 'update', 'partial_update', 'destroy': Must be an admin user.
        """
        if self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [IsAdminUser]
        else:
            permission_classes = [IsAuthenticated, IsAdminOrOwner]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """
        Filter orders to only show the user's own orders unless they are staff.
        """
        qs = super().get_queryset()
        if not self.request.user.is_staff:
            return qs.filter(user=self.request.user)
        return qs

    def create(self, request, *args, **kwargs):
        """
        Create a new order.
        The logic is handled by the OrderCreateSerializer.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = serializer.save()
        # After saving, serialize the created order object for the response
        response_serializer = OrderSerializer(order, context={'request': request})
        # Optionally, trigger post-creation tasks
        send_order_confirmation_email.delay(order.order_id)
        headers = self.get_success_headers(response_serializer.data)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED, headers=headers)
