from rest_framework import serializers

from shop.serializers import ProductSerializer


class CartSerializer(serializers.Serializer):
    class CartItemSerializer(serializers.Serializer):
        product = ProductSerializer()
        quantity = serializers.IntegerField(min_value=1)  # Ensure quantity is at least 1
        total_price = serializers.DecimalField(max_digits=10, decimal_places=2)

    items = CartItemSerializer(many=True)
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2)
