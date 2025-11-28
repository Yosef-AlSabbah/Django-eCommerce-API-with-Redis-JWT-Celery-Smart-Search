from decimal import Decimal
from django.db import transaction
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from account.models import Address
from cart.cart import Cart
from coupons.models import Coupon
from orders.models import Order, OrderItem
from shop.models import Product


class OrderItemSerializer(serializers.ModelSerializer):
    """
    Serializer for the OrderItem model.
    Provides detailed information about a product within an order.
    """
    product = serializers.StringRelatedField()
    price = serializers.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        model = OrderItem
        fields = ('product', 'quantity', 'price')


class OrderSerializer(serializers.ModelSerializer):
    """
    Serializer for the Order model (read-only).
    Provides comprehensive details about an order, including its items.
    """
    items = OrderItemSerializer(many=True, read_only=True)
    user = serializers.StringRelatedField()
    address = serializers.StringRelatedField()
    coupon = serializers.StringRelatedField()
    status = serializers.CharField(source='get_status_display')
    payment_status = serializers.CharField(source='get_payment_status_display')

    class Meta:
        model = Order
        fields = (
            'order_id', 'user', 'address', 'order_date', 'updated', 'status',
            'coupon', 'currency', 'discount_amount', 'payment_gateway',
            'payment_status', 'shipping_cost', 'shipping_provider',
            'shipping_tracking_code', 'subtotal', 'tax_amount', 'total_payable',
            'items'
        )


class OrderCreateSerializer(serializers.Serializer):
    """
    Serializer for creating a new order.
    Handles the logic of order creation from the user's cart.
    """
    address_id = serializers.IntegerField()
    coupon_code = serializers.CharField(required=False, allow_blank=True)

    def validate_address_id(self, value):
        """
        Validate that the address exists and belongs to the current user.
        """
        user = self.context['request'].user
        try:
            address = Address.objects.get(id=value, user=user)
        except Address.DoesNotExist:
            raise ValidationError('The selected address is invalid.')
        return address

    def validate(self, data):
        """
        Validate coupon against cart details.
        """
        cart = Cart(self.context['request'])
        coupon_code = data.get('coupon_code')

        if not coupon_code:
            data['coupon'] = None
            return data

        try:
            coupon = Coupon.objects.get(code__iexact=coupon_code, active=True)
        except Coupon.DoesNotExist:
            raise ValidationError({'coupon_code': 'The entered coupon is invalid.'})

        if not coupon.is_valid():
            raise ValidationError({'coupon_code': 'Coupon is not valid at this time.'})
        if coupon.usage_count >= coupon.max_usage:
            raise ValidationError({'coupon_code': 'This coupon has reached its usage limit.'})
        if cart.get_total_price() < coupon.min_purchase_amount:
            raise ValidationError({
                'coupon_code': f"A minimum purchase of {coupon.min_purchase_amount} is required to use this coupon."
            })

        data['coupon'] = coupon
        return data

    def save(self, **kwargs):
        """
        Create and save the order and its items from the cart.
        """
        cart = Cart(self.context['request'])
        if len(cart) == 0:
            raise ValidationError('Your cart is empty.')

        validated_data = self.validated_data
        address = validated_data['address_id']
        coupon = validated_data.get('coupon')
        user = self.context['request'].user

        with transaction.atomic():
            # Create the order
            order = Order.objects.create(
                user=user,
                address=address,
                coupon=coupon,
                discount_amount=cart.get_discount(coupon) if coupon else 0
            )

            if coupon:
                coupon.increment_usage_count()

            # Create order items and update product stock
            items_to_create = []
            products_to_update = []

            for item in cart:
                product = item['product']
                if product.stock < item['quantity']:
                    raise ValidationError(f"Not enough stock for {product.name}.")

                product.stock -= item['quantity']
                products_to_update.append(product)

                items_to_create.append(
                    OrderItem(
                        order=order,
                        product=product,
                        quantity=item['quantity']
                    )
                )

            OrderItem.objects.bulk_create(items_to_create)
            Product.objects.bulk_update(products_to_update, ['stock'])

            # Set shipping and tax (assuming fixed values for now)
            order.shipping_cost = Decimal('15.00')
            order.tax_amount = order.get_total_cost_before_discount() * Decimal('0.09')

            # Calculate final order total
            order.calculate_total_payable()
            order.save()

            # Clear the cart
            cart.clear()

            return order
