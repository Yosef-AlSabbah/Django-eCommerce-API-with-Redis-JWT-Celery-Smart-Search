from rest_framework import serializers

from orders.models import OrderItem, Order
from shop.serializers import ProductSerializer


class OrderSerializer(serializers.ModelSerializer):
    class OrderItemSerializer(serializers.ModelSerializer):
        product = ProductSerializer(many=False, read_only=True)
        price = serializers.DecimalField(max_digits=10, decimal_places=2)

        class Meta:
            model = OrderItem
            fields = ['product', 'quantity', 'price']

    order_id = serializers.UUIDField(read_only=True)
    order_items = OrderItemSerializer(many=True, read_only=True, source='items')
    user = serializers.ReadOnlyField(source='user.username')
    coupon = serializers.CharField(source='coupon.code', default=None)
    discount = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        source='get_discount',
        read_only=True
    )
    original_price = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        source='get_total_cost_before_discount',
        read_only=True
    )
    total_price = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        read_only=True
    )
    status = serializers.ChoiceField(choices=Order.Status.choices)

    class Meta:
        model = Order
        fields = ['order_id', 'user', 'quantity', 'order_date', 'order_items', 'original_price', 'total_price',
                  'coupon', 'discount', 'status']
        read_only_fields = ['user', 'order_date']

    def update(self, instance, validated_data):
        # Check if status is in the incoming data and the user is allowed to update it
        request = self.context.get('request')
        if request and request.user.is_staff and 'status' in validated_data:
            instance.status = validated_data.pop('status')
        # Update other fields if needed
        return super().update(instance, validated_data)
