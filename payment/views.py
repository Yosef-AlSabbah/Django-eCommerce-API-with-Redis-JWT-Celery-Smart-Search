from decimal import Decimal
from logging import getLogger

import stripe
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.urls import reverse
from drf_spectacular.utils import extend_schema, OpenApiResponse, extend_schema_view
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from orders.models import Order

logger = getLogger(__name__)

stripe.api_key = settings.STRIPE_SECRET_KEY
stripe.api_version = settings.STRIPE_API_VERSION


@extend_schema_view(
    post=extend_schema(
        operation_id="payment_process",
        description="Create a Stripe checkout session for an order. Expects an order_id in request data.",
        tags=["Payments"],
        responses={
            201: OpenApiResponse(description="Stripe session created successfully with payment URL."),
            400: OpenApiResponse(description="Order ID is missing or invalid request data.")
        },
    )
)
class PaymentProcessAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        """
        Handles the creation of a Stripe checkout session for a given order.

        This method expects an `order_id` in the request data and performs the following:
        - Validates the presence of the `order_id`.
        - Retrieves the order associated with the authenticated user.
        - Checks if the order has already been paid.
        - Creates a Stripe checkout session with the order details, including line items and discounts.
        - Returns the payment URL for the created session.

        Returns:
            - 400 Bad Request if the `order_id` is missing, invalid, or the order is already paid.
            - 201 Created with the Stripe payment URL if the session is successfully created.
        """
        # Retrieve the order_id from the request's kwargs
        order_id = kwargs.get("order_id")
        if not order_id:
            # Log an error and return a 400 response if order_id is missing
            logger.error("Order ID is missing in payment process request.")
            return Response({"error": "Order ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        # Fetch the order associated with the authenticated user or return 404 if not found
        order = get_object_or_404(Order, order_id=order_id, user=request.user)

        # Check if the order is already paid and return a 400 response if true
        if order.status in [Order.Status.COMPLETED, Order.Status.CANCELLED]:
            logger.info("Order ID %s is already paid.", order_id)
            return Response({"message": "This order has already been paid."}, status=status.HTTP_400_BAD_REQUEST)

        # Build success and cancel URLs for the Stripe checkout session
        success_url = request.build_absolute_uri(reverse("payment:completed"))
        cancel_url = request.build_absolute_uri(reverse("payment:canceled"))

        # Prepare the session data for Stripe checkout
        session_data = {
            "mode": "payment",
            "client_reference_id": order.order_id,
            "success_url": success_url,
            "cancel_url": cancel_url,
            "line_items": []
        }

        try:
            # Add line items to the session data for each item in the order
            for item in order.items.all():
                # Check if the stock is sufficient for the requested quantity
                if item.product.stock < item.quantity:
                    logger.error("Insufficient stock for product: %s", item.product.name)
                    return Response(
                        {"error": f"Insufficient stock for product: {item.product.name}"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            # If all stock checks pass, decrement the stock for each product
            for item in order.items.all():
                item.product.stock -= item.quantity
                item.product.save()

                session_data["line_items"].append(
                    {
                        "price_data": {
                            "unit_amount": int(item.product.price * Decimal('100')),  # Convert price to cents
                            "currency": "usd",
                            "product_data": {
                                "name": item.product.name,  # Use the product name
                            },
                        },
                        "quantity": item.quantity,  # Add the quantity of the item
                    }
                )

            # If a valid coupon exists, create a Stripe coupon and add it to the session data
            if order.coupon and order.coupon.is_valid():
                stripe_coupon = stripe.Coupon.create(
                    name=order.coupon.code,
                    percent_off=order.coupon.discount,
                    duration='once'
                )
                session_data['discounts'] = [{'coupon': stripe_coupon.id}]

            # Remove the coupon_id from the session if it exists
            if 'coupon_id' in request.session:
                del request.session['coupon_id']

            # Create the Stripe checkout session
            session = stripe.checkout.Session.create(**session_data)
            logger.info("Stripe session created for order id: %s", order.order_id)
            # Return the payment URL in the response
            return Response({"payment_url": session.url}, status=status.HTTP_201_CREATED)
        except Exception as e:
            # Log the error and return a 400 response if session creation fails
            logger.error("Error creating Stripe session for order id: %s: %s", order.order_id, e, exc_info=True)
            return Response({"error": "There was an error processing your payment."},
                            status=status.HTTP_400_BAD_REQUEST)


@extend_schema_view(
    get=extend_schema(
        operation_id="payment_completed",
        description="Handle successful payment completion.",
        tags=["Payments"],
        responses={
            200: OpenApiResponse(description="Payment completed successfully.")
        },
    )
)
class PaymentCompletedAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Handles the successful completion of a payment.

        This method logs the payment completion for the authenticated user and returns a success message.

        Returns:
            - 200 OK with a message indicating successful payment completion.
        """
        logger.info("Payment completed for user id: %s", request.user.id)
        return Response({"message": "Payment completed successfully."}, status=status.HTTP_200_OK)


@extend_schema_view(
    get=extend_schema(
        operation_id="payment_canceled",
        description="Handle payment cancellation and cleanup if necessary.",
        tags=["Payments"],
        responses={
            200: OpenApiResponse(description="Payment canceled.")
        },
    )
)
class PaymentCanceledAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Handles the cancellation of a payment.

        This method logs the payment cancellation for the authenticated user and returns a cancellation message.

        Returns:
            - 200 OK with a message indicating the payment was canceled.
        """
        logger.info("Payment canceled for user id: %s", request.user.id)
        return Response({"message": "Payment canceled."}, status=status.HTTP_200_OK)
