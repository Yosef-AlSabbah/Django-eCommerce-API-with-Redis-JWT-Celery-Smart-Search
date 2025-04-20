from rest_framework import permissions, viewsets
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response

from cart.cart import Cart
from .models import Order, OrderItem
from .serializers import OrderSerializer
from .tasks import send_order_confirmation_email


class OrderViewSet(viewsets.ModelViewSet):
    """
    OrderViewSet

    This class is a Django REST Framework (DRF) `ModelViewSet` for managing `Order` objects via the API.
    It provides functionality for listing, retrieving, and managing orders, while restricting certain actions
    like order creation.

    Attributes:
        queryset (QuerySet): A queryset that prefetches related `OrderItem` and `Product` objects for optimization.
        serializer_class (Serializer): The serializer class used for serializing and deserializing `Order` objects.
        permission_classes (list): The default permission classes applied to the viewset.

    Methods:
        get_permissions():
            Dynamically assigns permissions based on the action being performed.
            - For `list` and `retrieve` actions, authenticated users are allowed.
            - For other actions, only admin users are allowed.

        create(request, *args, **kwargs):
            Disables the creation of orders via the API. Returns a 403 Forbidden response.
    """
    queryset = Order.objects.prefetch_related('items__product')
    serializer_class = OrderSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        """
        Retrieve the queryset for the viewset, with optimizations and user-specific filtering.

        This method overrides the default `get_queryset` to include prefetching of related objects
        for performance optimization. Additionally, it applies user-specific filtering for non-staff users.

        Returns:
            QuerySet: A queryset of `Order` objects, filtered by the logged-in user if the user is not staff,
            or prefetching related `OrderItem` and `Product` objects for staff users.
        """
        qs = super().get_queryset()
        if not self.request.user.is_staff:
            # If the user is not staff, filter orders by the logged-in user
            return qs.filter(user=self.request.user)
        return qs.distinct().prefetch_related('items__product')

    def get_permissions(self):
        """
        Assign permissions based on the action being performed.
        """
        if self.action in ['update', 'partial_update', 'destroy']:
            self.permission_classes = [permissions.IsAdminUser]
        else:
            self.permission_classes = [IsAuthenticated]
        return super().get_permissions()

    def create(self, request, *args, **kwargs):
        """
        Handle the creation of an order via the API.

        Args:
            request: The HTTP request object containing the order data.

        Returns:
            Response: A JSON response with the created order details or an error message.
        """
        cart = Cart(request)

        # Check if the cart is empty
        if len(cart) == 0:
            return Response({"error": "You cannot place an order with an empty cart."}, status=400)

        # Create the order
        order = Order.objects.create(
            user=request.user,
            quantity=len(cart),
            status=Order.Status.PENDING
        )

        # Add items to the order
        for item in cart:
            OrderItem.objects.create(
                order=order,
                product=item['product'],
                quantity=item['quantity']
            )

        # Clear the cart
        cart.clear()

        # Launch asynchronous task
        send_order_confirmation_email.delay(order.order_id)

        # Return the created order details
        serializer = self.get_serializer(order)
        return Response(serializer.data, status=201)
