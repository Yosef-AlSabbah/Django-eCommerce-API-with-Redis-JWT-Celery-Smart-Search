from logging import getLogger

from django.shortcuts import get_object_or_404
from django.urls import reverse
from drf_spectacular.utils import extend_schema, OpenApiResponse, extend_schema_view
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ecommerce_api.core.api_standard_response import ApiResponse
from orders.models import Order
from .gateways import ZibalGateway
from shipping.tasks import create_postex_shipment_task

logger = getLogger(__name__)


@extend_schema_view(
    post=extend_schema(
        operation_id="payment_process",
        description="Create a Zibal payment request for an order. Expects an order_id in request data.",
        tags=["Payments"],
        responses={
            201: OpenApiResponse(description="Zibal payment URL created successfully."),
            400: OpenApiResponse(description="Order ID is missing or invalid request data.")
        },
    )
)
class PaymentProcessAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        order_id = kwargs.get("order_id")
        if not order_id:
            return ApiResponse.error(
                message="Order ID is required.",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        order = get_object_or_404(Order, order_id=order_id, user=request.user)

        if order.payment_status == Order.PaymentStatus.SUCCESS:
            return ApiResponse.error(
                message="This order has already been paid.",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        # Check stock before creating payment request
        for item in order.items.all():
            if item.product.stock < item.quantity:
                return ApiResponse.error(
                    message=f"Insufficient stock for product: {item.product.name}",
                    status_code=status.HTTP_400_BAD_REQUEST
                )

        callback_url = request.build_absolute_uri(reverse("payment:verify"))

        gateway = ZibalGateway()
        response = gateway.create_payment_request(
            amount=int(order.total_payable * 10),  # Convert Toman to Rial for Zibal API
            order_id=order.order_id,
            callback_url=callback_url
        )

        if response.get('result') == 100:
            order.payment_gateway = 'zibal'
            order.payment_track_id = response.get('trackId')
            order.save()
            payment_url = f"https://gateway.zibal.ir/start/{response.get('trackId')}"
            return ApiResponse.success(
                data={"payment_url": payment_url},
                status_code=status.HTTP_201_CREATED
            )
        else:
            return ApiResponse.error(
                message="Failed to create payment request.",
                status_code=status.HTTP_400_BAD_REQUEST
            )


@extend_schema_view(
    get=extend_schema(
        operation_id="payment_verify",
        description="Verify a Zibal payment.",
        tags=["Payments"],
        responses={
            200: OpenApiResponse(description="Payment verified successfully."),
            400: OpenApiResponse(description="Invalid payment verification request.")
        },
    )
)
class PaymentVerifyAPIView(APIView):
    def get(self, request, *args, **kwargs):
        track_id = request.query_params.get('trackId')
        if not track_id:
            return ApiResponse.error(
                message="trackId is required.",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        try:
            order = Order.objects.get(payment_track_id=track_id)
        except Order.DoesNotExist:
            return ApiResponse.error(
                message="Order not found.",
                status_code=status.HTTP_404_NOT_FOUND
            )

        gateway = ZibalGateway()
        response = gateway.verify_payment(track_id)

        if response.get('result') == 100:
            # Check stock again before finalizing the order
            for item in order.items.all():
                if item.product.stock < item.quantity:
                    # Handle insufficient stock after payment (e.g., refund or notify admin)
                    order.payment_status = Order.PaymentStatus.FAILED
                    order.save()
                    return ApiResponse.error(
                        message=f"Insufficient stock for product: {item.product.name}. Payment will be refunded.",
                        status_code=status.HTTP_400_BAD_REQUEST
                    )

            # Decrement stock
            for item in order.items.all():
                item.product.stock -= item.quantity
                item.product.save()

            order.payment_status = Order.PaymentStatus.SUCCESS
            order.payment_ref_id = response.get('refNumber')
            order.status = Order.Status.PAID
            order.save()

            # Create shipment asynchronously
            create_postex_shipment_task.delay(order.order_id)

            return ApiResponse.success(
                message="Payment verified. Shipment creation is in progress.",
                status_code=status.HTTP_200_OK
            )
        else:
            order.payment_status = Order.PaymentStatus.FAILED
            order.save()
            return ApiResponse.error(
                message="Payment verification failed.",
                status_code=status.HTTP_400_BAD_REQUEST
            )
