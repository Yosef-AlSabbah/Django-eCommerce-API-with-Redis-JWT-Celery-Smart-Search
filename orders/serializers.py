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
    user = serializers.ReadOnlyField(source='user.username')
    coupon = serializers.ReadOnlyField(source='coupon.code')
    discount = serializers.ReadOnlyField(source='get_discount')
    original_price = serializers.ReadOnlyField(source='get_total_cost_before_discount')

    class Meta:
        model = Order
        fields = ['order_id', 'user', 'quantity', 'order_date', 'order_items', 'original_price', 'total_price',
                  'coupon', 'discount']
        read_only_fields = ['user', 'order_date']
