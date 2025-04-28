from logging import getLogger

from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter, extend_schema_view
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ecommerce_api.core.mixins import PaginationMixin
from shop.models import Product
from .models import Message

logger = getLogger(__name__)


@extend_schema_view(
    get=extend_schema(
        operation_id="product_chat_retrieve",
        description="Retrieve paginated chat messages for a specific product.",
        tags=["Chat"],
        parameters=[
            OpenApiParameter(name="page", type=int, description="Page number (default: 1)", required=False),
            OpenApiParameter(name="page_size", type=int,
                             description="Number of messages per page (default: 5, max: 50)", required=False),
        ],
        responses={
            200: OpenApiResponse(description="Paginated chat messages retrieved successfully."),
            404: OpenApiResponse(description="Product not found."),
        },
    )
)
class ProductChatAPIView(PaginationMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, product_id):
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist as e:
            logger.error(f"Product not found for id {product_id}: {e}", exc_info=True)
            return Response({"error": "Product not found."}, status=404)

        try:
            messages = Message.objects.filter(product=product).select_related("sender", "recipient").order_by("-id")
            paginator = self.pagination_class()
            paginated_messages = paginator.paginate_queryset(messages, request)
            messages_data = [
                {
                    "sender": message.sender.username,
                    "recipient": message.recipient.username,
                    "content": message.content,
                    "timestamp": message.created_at,
                }
                for message in reversed(paginated_messages)
            ]
            return paginator.get_paginated_response({
                "product": product.name,
                "product_url": product.get_absolute_url(),
                "messages": messages_data
            })
        except Exception as e:
            logger.error(f"Error retrieving chat messages for product id {product_id}: {e}", exc_info=True)
            return Response({"error": "An error occurred retrieving chat messages."}, status=500)
