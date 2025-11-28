from logging import getLogger

from drf_spectacular.utils import (
    extend_schema,
    OpenApiResponse,
    extend_schema_view,
)
from django.db import transaction
from rest_framework import viewsets, status
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response

from cart.cart import Cart
from coupons.models import Coupon
from .models import Order, OrderItem
from .permissions import IsAdminOrOwner
from .serializers import OrderSerializer
from .tasks import send_order_confirmation_email

logger = getLogger(__name__)


@extend_schema_view(
    list=extend_schema(
        operation_id="order_list",
        description="List orders. Non-staff users see only their orders.",
        tags=["Orders"],
        responses={
            200: OpenApiResponse(description="List of orders retrieved successfully."),
        },
        request=None,
    ),
    retrieve=extend_schema(
        operation_id="order_retrieve",
        description="Retrieve an order by its ID.",
        tags=["Orders"],
        responses={
            200: OpenApiResponse(description="Order details retrieved successfully."),
            404: OpenApiResponse(description="Order not found."),
        },
    ),
    create=extend_schema(
        operation_id="order_create",
        description="Create an order from the cart. Returns an error if the cart is empty.",
        tags=["Orders"],
        responses={
            201: OpenApiResponse(description="Order created successfully."),
            400: OpenApiResponse(description="You cannot place an order with an empty cart or bad request."),
        },
    ),
    update=extend_schema(
        operation_id="order_update",
        description="Update an order. Admin access required.",
        tags=["Orders"],
        responses={
            200: OpenApiResponse(description="Order updated successfully."),
        },
    ),
    partial_update=extend_schema(
        operation_id="order_partial_update",
        description="Partially update an order. Admin access required.",
        tags=["Orders"],
        responses={
            200: OpenApiResponse(description="Order partially updated successfully."),
        },
    ),
    destroy=extend_schema(
        operation_id="order_destroy",
        description="Delete an order. Admin access required.",
        tags=["Orders"],
        responses={
            200: OpenApiResponse(description="Order deleted successfully."),
        },
    ),
)
class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.prefetch_related('items__product')
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated, IsAdminOrOwner]

    def get_queryset(self):
        qs = super().get_queryset()
        if not self.request.user.is_staff:
            return qs.filter(user=self.request.user)
        return qs.distinct().prefetch_related('items__product')

    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [IsAdminUser]
        else:
            permission_classes = [IsAdminOrOwner]
        return [permission() for permission in permission_classes]

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        logger.info("Creating order for user id: %s", request.user.id)
        try:
            cart = Cart(request)
            if len(cart) == 0:
                logger.warning("Empty cart for user id: %s", request.user.id)
                return Response({"error": "You cannot place an order with an empty cart."},
                                status=status.HTTP_400_BAD_REQUEST)
            coupon = None
            try:
                coupon_id = request.session.get('coupon_id', None)
                if coupon_id:
                    coupon = Coupon.objects.get(id=request.session['coupon_id'])
            except Coupon.DoesNotExist:
                logger.warning("Invalid coupon ID in session for user id: %s", request.user.id)
                return Response({"error": "Invalid coupon."}, status=status.HTTP_400_BAD_REQUEST)

            if coupon:
                if not coupon.is_valid():
                    return Response(
                        {"detail": "Coupon is not valid at this time."},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                if coupon.usage_count >= coupon.max_usage:
                    return Response(
                        {"detail": "This coupon has reached its usage limit."},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                if cart.get_total_price() < coupon.min_purchase_amount:
                    return Response(
                        {"detail": f"A minimum purchase of {coupon.min_purchase_amount} is required to use this coupon."},
                        status=status.HTTP_400_BAD_REQUEST
                    )

            order = Order.objects.create(
                user=request.user,
                quantity=len(cart),
                status=Order.Status.PENDING,
                coupon=coupon,
            )

            for item in cart:
                OrderItem.objects.create(
                    order=order,
                    product=item['product'],
                    quantity=item['quantity']
                )

            if coupon:
                coupon.increment_usage_count()

            cart.clear()
            send_order_confirmation_email.delay(order.order_id)
            serializer = self.get_serializer(order)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error("Error creating order for user id: %s: %s", request.user.id, e, exc_info=True)
            raise
