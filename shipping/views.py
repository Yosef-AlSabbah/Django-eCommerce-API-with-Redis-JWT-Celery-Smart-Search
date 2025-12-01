from rest_framework.views import APIView
from rest_framework import status
from django.shortcuts import get_object_or_404
from orders.models import Order
from .providers import PostexShippingProvider
from ecommerce_api.core.api_standard_response import ApiResponse

class CityListAPIView(APIView):
    def get(self, request, *args, **kwargs):
        provider = PostexShippingProvider()
        response = provider.get_cities()

        if response.get('error'):
            return ApiResponse.error(message='Failed to get city list', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return ApiResponse.success(data=response, status_code=status.HTTP_200_OK)


class CalculateShippingCostAPIView(APIView):
    def post(self, request, *args, **kwargs):
        order_id = request.data.get('order_id')
        if not order_id:
            return ApiResponse.error(message='Order ID is required', status_code=status.HTTP_400_BAD_REQUEST)

        order = get_object_or_404(Order, order_id=order_id)

        if not order.address:
            return ApiResponse.error(message='Order address is not set', status_code=status.HTTP_400_BAD_REQUEST)

        provider = PostexShippingProvider()
        response = provider.get_shipping_quote(order)

        if response.get('error') or not response.get('data'):
            return ApiResponse.error(message='Failed to get shipping cost', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Assuming the first quote is the desired one
        shipping_cost = response['data'][0].get('price', 0)

        order.shipping_cost = shipping_cost
        order.save()

        return ApiResponse.success(data={'shipping_cost': shipping_cost}, status_code=status.HTTP_200_OK)
