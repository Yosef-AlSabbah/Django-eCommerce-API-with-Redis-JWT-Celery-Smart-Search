import decimal

from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from shop.serializers import ProductSerializer


class CartSerializer(serializers.Serializer):
    class CartItemSerializer(serializers.Serializer):
        product = ProductSerializer()
        quantity = serializers.IntegerField(min_value=1)  # Ensure quantity is at least 1
        total_price = serializers.DecimalField(max_digits=10, decimal_places=2)

    items = CartItemSerializer(many=True)
    coupon = serializers.SerializerMethodField()
    total_price = serializers.SerializerMethodField()

    @extend_schema_field(serializers.DictField(child=serializers.CharField(), allow_null=True))
    def get_coupon(self, obj):
        """
        Get the coupon code and discount applied to the cart.
        """
        request = self.context.get('request')
        coupon_id = request.session.get('coupon_id')
        if not coupon_id:
            return None

        from coupons.models import Coupon
        try:
            coupon = Coupon.objects.get(id=coupon_id, active=True)
            return {"code": coupon.code, "discount": coupon.discount}
        except Coupon.DoesNotExist:
            return None

    @extend_schema_field(serializers.DictField(child=serializers.DecimalField(max_digits=10, decimal_places=2)))
    def get_total_price(self, obj):
        """
        Calculate the final total price with and without the discount.
        """
        total_price = obj.get('total_price', 0)
        coupon_data = self.get_coupon(obj)
        if coupon_data:
            discount = total_price * (decimal.Decimal(coupon_data['discount']) / decimal.Decimal(100))
            return {
                "without_discount": total_price,
                "with_discount": total_price - discount
            }
        return {"without_discount": total_price, "with_discount": total_price}


class AddToCartSerializer(serializers.Serializer):
    quantity = serializers.IntegerField(min_value=1, default=1)
    override = serializers.BooleanField(default=False)
