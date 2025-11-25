from django.test import TestCase
from django.contrib.auth import get_user_model
from decimal import Decimal
from .models import Order, OrderItem
from shop.models import Product, Category
from coupons.models import Coupon
from account.models import Address
from django.utils import timezone
from datetime import timedelta

User = get_user_model()


class OrderModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='test@example.com', password='password')
        self.category = Category.objects.create(name='Test Category')
        self.product = Product.objects.create(
            name='Test Product', category=self.category, price=Decimal('100.00'), stock=10, user=self.user,
            weight=1, length=1, width=1, height=1
        )
        self.address = Address.objects.create(user=self.user, city='Tehran', province='Tehran', full_address='123 Main St', postal_code='12345')

    def test_order_creation_and_total_calculation(self):
        order = Order.objects.create(user=self.user, address=self.address)
        OrderItem.objects.create(order=order, product=self.product, quantity=2)
        order.shipping_cost = Decimal('15.00')
        order.tax_amount = Decimal('10.00')
        order.save()

        self.assertEqual(order.subtotal, Decimal('200.00'))
        self.assertEqual(order.total_payable, Decimal('225.00'))

    def test_order_with_coupon(self):
        coupon = Coupon.objects.create(
            code='TEST',
            discount=10,
            valid_from=timezone.now() - timedelta(days=1),
            valid_to=timezone.now() + timedelta(days=1)
        )
        order = Order.objects.create(user=self.user, address=self.address, coupon=coupon)
        OrderItem.objects.create(order=order, product=self.product, quantity=1)
        order.save()

        self.assertEqual(order.subtotal, Decimal('100.00'))
        self.assertEqual(order.discount_amount, Decimal('10.00'))
        self.assertEqual(order.total_payable, Decimal('90.00'))
