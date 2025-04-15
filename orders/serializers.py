from rest_framework import serializers

from orders.models import OrderItem, Order
from shop.serializers import ProductSerializer


class OrderSerializer(serializers.ModelSerializer):
    class OrderItemSerializer(serializers.ModelSerializer):
        product = ProductSerializer(many=False, read_only=True)

        class Meta:
            model = OrderItem
            fields = ['product', 'quantity', 'price']

    order_items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ['user', 'quantity', 'order_date', 'order_items', 'total_price']
        read_only_fields = ['user', 'order_date']
