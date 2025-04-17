from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from shop.models import Product
from .cart import Cart
from .serializers import CartSerializer


class CartAPIView(APIView):
    """
    API view to handle cart operations such as viewing, adding/updating,
    and removing items from the cart.
    """
    http_method_names = ['get', 'post', 'delete']

    def get(self, request):
        """
        Retrieve the cart details, including all items and the total price.

        Args:
            request: The HTTP request object.

        Returns:
            Response: A JSON response containing the cart items and total price.
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
        serializer = CartSerializer(cart_data)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, product_id):
        """
        Add a product to the cart or update its quantity.

        Args:
            request: The HTTP request object containing the product data.
            product_id: The ID of the product to add or update.

        Returns:
            Response: A JSON response indicating the operation's success.
        """
        cart = Cart(request)
        product = get_object_or_404(Product, product_id=product_id)
        try:
            quantity = int(request.data.get('quantity', 1))
            override_quantity = request.data.get('override', False)
            cart.add(product=product, quantity=quantity, override_quantity=override_quantity)
            return Response(
                {'message': 'Product added/updated in cart'},
                status=status.HTTP_200_OK
            )
        except ValueError:
            return Response(
                {'error': 'Invalid quantity provided'},
                status=status.HTTP_400_BAD_REQUEST
            )

    def delete(self, request, product_id):
        """
        Remove a product from the cart.

        Args:
            request: The HTTP request object.
            product_id: The ID of the product to remove.

        Returns:
            Response: A JSON response indicating the operation's success.
        """
        cart = Cart(request)
        product = get_object_or_404(Product, product_id=product_id)
        cart.remove(product)
        return Response(
            {'message': 'Product removed from cart'},
            status=status.HTTP_200_OK
        )
