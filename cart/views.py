from logging import getLogger

from django.shortcuts import get_object_or_404
from drf_spectacular.utils import (
    extend_schema,
    OpenApiResponse,
    extend_schema_view,
)
from rest_framework import status, mixins, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from shop.models import Product
from .cart import Cart
from .serializers import CartSerializer, AddToCartSerializer

logger = getLogger(__name__)


@extend_schema_view(
    list=extend_schema(
        operation_id="cart_retrieve_list",
        description="Retrieve the cart details, including all items and the total price.",
        tags=["Cart"],
        responses={
            200: OpenApiResponse(
                response=CartSerializer,
                description="Cart details retrieved successfully."
            ),
        },
    ),
    add_to_cart=extend_schema(
        operation_id="cart_add_product",
        description="Add a product to the cart or update its quantity.",
        tags=["Cart"],
        request=AddToCartSerializer,
        responses={
            200: OpenApiResponse(description="Product added/updated in cart."),
            400: OpenApiResponse(description="Invalid quantity provided."),
            404: OpenApiResponse(description="Product not found."),
        },
    ),
    remove_from_cart=extend_schema(
        operation_id="cart_remove_product",
        description="Remove a product from the cart.",
        tags=["Cart"],
        responses={
            200: OpenApiResponse(description="Product removed from cart."),
            404: OpenApiResponse(description="Product not found."),
        },
    ),
)
class CartViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """
    A viewset for viewing and editing cart items.
    """
    lookup_field = 'product_id'
    lookup_url_kwarg = 'product_id'

    @extend_schema(
        operation_id="cart_get_details",
        description="Get the current cart contents with total price.",
        tags=["Cart"],
        responses={
            200: OpenApiResponse(
                response=CartSerializer,
                description="Cart details retrieved successfully."
            ),
        },
    )
    def list(self, request, *args, **kwargs):
        """
        Retrieve the cart details, including all items and the total price.

        Args:
            request: The HTTP request object.

        Returns:
            Response: A JSON response containing the cart details and total price.
        """
        cart = Cart(request)
        cart_data = {
            'items': [
                {
                    'product': item['product'],
                    'quantity': item['quantity'],
                    'total_price': item['total_price'],
                }
                for item in cart
            ],
            'total_price': cart.get_total_price(),
        }
        serializer = serializer = CartSerializer(cart_data, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='add')
    @extend_schema(
        operation_id="cart_add_product",
        description="Add or update a product in the cart.",
        tags=["Cart"],
        request=AddToCartSerializer,
        responses={
            200: OpenApiResponse(description="Product added/updated in cart."),
            400: OpenApiResponse(description="Invalid quantity provided."),
            404: OpenApiResponse(description="Product not found."),
        },
    )
    def add_to_cart(self, request, product_id=None):
        """
        Add a product to the cart or update its quantity.

        Args:
            request: The HTTP request object containing the product data.
            product_id: The ID of the product to add or update.

        Returns:
            Response: A JSON response indicating success or failure.
        """
        cart = Cart(request)
        product = get_object_or_404(Product, product_id=product_id)
        serializer = AddToCartSerializer(data=request.data)

        if serializer.is_valid():
            data = serializer.validated_data
            cart.add(
                product=product,
                quantity=data['quantity'],
                override_quantity=data['override']
            )
            return Response(
                {'message': 'Product added/updated in cart'},
                status=status.HTTP_200_OK
            )
        else:
            logger.error(f"Invalid data provided in cart post: {serializer.errors}")
            return Response(
                {'error': 'Invalid data provided', 'details': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['delete'], url_path='remove')
    @extend_schema(
        operation_id="cart_remove_product",
        description="Remove a product from the cart.",
        tags=["Cart"],
        responses={
            200: OpenApiResponse(description="Product removed from cart."),
            404: OpenApiResponse(description="Product not found."),
        },
    )
    def remove_from_cart(self, request, product_id=None):
        """
        Remove a product from the cart.

        Args:
            request: The HTTP request object.
            product_id: The ID of the product to remove.

        Returns:
            Response: A JSON response indicating success or failure.
        """
        cart = Cart(request)
        product = get_object_or_404(Product, product_id=product_id)
        try:
            cart.remove(product)
            return Response(
                {'message': 'Product removed from cart'},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error removing product from cart: {e}", exc_info=True)
            raise
