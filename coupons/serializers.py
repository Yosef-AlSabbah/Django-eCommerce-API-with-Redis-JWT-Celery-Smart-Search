from rest_framework import serializers

from .models import Coupon


class CouponSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coupon
        fields = ['code', 'valid_from', 'valid_to', 'discount', 'active']

    def validate(self, data):
        if data['valid_from'] >= data['valid_to']:
            raise serializers.ValidationError("`valid_from` must be earlier than `valid_to`.")
        if data['discount'] <= 0:
            raise serializers.ValidationError("`discount` must be greater than zero.")
        return data
