from logging import getLogger

from drf_spectacular.utils import extend_schema, OpenApiResponse, extend_schema_view
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from cart.cart import Cart
from coupons.models import Coupon
from coupons.serializers import CouponSerializer

logger = getLogger(__name__)


@extend_schema_view(
    list=extend_schema(
        operation_id="coupon_list",
        description="Only staff can list coupons.",
        tags=["Coupons"],
    ),
    retrieve=extend_schema(
        operation_id="coupon_retrieve",
        description="Only staff can retrieve a coupon.",
        tags=["Coupons"],
    ),
    create=extend_schema(
        operation_id="coupon_create",
        description="Only staff can create a coupon.",
        tags=["Coupons"],
    ),
    update=extend_schema(
        operation_id="coupon_update",
        description="Only staff can update a coupon. Prevent modification of the `code` field.",
        tags=["Coupons"],
        responses={
            200: OpenApiResponse(description="Coupon updated successfully."),
            400: OpenApiResponse(description="Coupon code cannot be modified or bad request."),
        },
    ),
    partial_update=extend_schema(
        operation_id="coupon_partial_update",
        description="Only staff can partially update a coupon. Prevent modification of the `code` field.",
        tags=["Coupons"],
        responses={
            200: OpenApiResponse(description="Coupon updated successfully."),
            400: OpenApiResponse(description="Coupon code cannot be modified or bad request."),
        },
    ),
    destroy=extend_schema(
        operation_id="coupon_destroy",
        description="Only staff can delete a coupon. Mark the coupon as inactive instead.",
        tags=["Coupons"],
        responses={
            200: OpenApiResponse(description="Coupon has been marked as inactive."),
        },
    ),
    apply=extend_schema(
        operation_id="coupon_apply",
        description="Apply a coupon by its code.",
        tags=["Coupons"],
        responses={
            200: OpenApiResponse(description="Coupon applied successfully."),
            400: OpenApiResponse(description="Coupon code is required or coupon is not valid at this time."),
            404: OpenApiResponse(description="Invalid or inactive coupon code."),
        },
    ),
)
class CouponViewSet(viewsets.ModelViewSet):
    queryset = Coupon.objects.all()
    serializer_class = CouponSerializer
    permission_classes = [permissions.IsAdminUser]

    def update(self, request, *args, **kwargs):
        """
        Prevent modification of the `code` field.
        """
        try:
            partial = kwargs.pop('partial', False)
            instance = self.get_object()
            if 'code' in request.data and request.data['code'] != instance.code:
                return Response(
                    {"detail": "Coupon code cannot be modified."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            serializer = self.get_serializer(instance, data=request.data, partial=partial)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Error updating coupon: {e}", exc_info=True)
            raise

    def destroy(self, request, *args, **kwargs):
        """
        Mark the coupon as inactive instead of deleting it.
        """
        try:
            instance = self.get_object()
            instance.active = False
            instance.save()
            return Response(
                {"detail": "Coupon has been marked as inactive."},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error deactivating coupon: {e}", exc_info=True)
            raise

    @action(
        detail=False,
        methods=['post'],
        url_path='apply-coupon',
        url_name='apply-coupon',
        permission_classes=[permissions.AllowAny]
    )
    def apply(self, request):
        """
        Apply a coupon by its code.
        """
        try:
            cart = Cart(request)
            code = request.data.get('code')
            if not code:
                return Response(
                    {"detail": "Coupon code is required."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            try:
                coupon = Coupon.objects.get(code__iexact=code, active=True)
            except Coupon.DoesNotExist:
                return Response(
                    {"detail": "Invalid or inactive coupon code."},
                    status=status.HTTP_404_NOT_FOUND
                )

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

            request.session['coupon_id'] = coupon.id
            return Response(
                {"detail": "Coupon applied successfully.", "discount": coupon.discount},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error applying coupon: {e}", exc_info=True)
            raise
