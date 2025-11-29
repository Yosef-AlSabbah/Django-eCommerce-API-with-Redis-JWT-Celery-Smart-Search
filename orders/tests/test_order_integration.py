from decimal import Decimal
from django.utils import timezone
from datetime import timedelta
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from shop.models import Product, Category
from coupons.models import Coupon
from account.models import Address

User = get_user_model()


class OrderIntegrationTest(APITestCase):
    """
    Integration test for the complete order process.
    """

    def setUp(self):
        """
        Set up the necessary objects for the test.
        """
        # Create a user
        self.user = User.objects.create_user(
            email='testuser@example.com',
            password='testpassword123',
            first_name='Test',
            last_name='User'
        )
        self.user.is_active = True
        self.user.save()

        # Create a category
        self.category = Category.objects.create(name='Electronics', slug='electronics')

        # Create a product
        self.product = Product.objects.create(
            name='Test Product',
            slug='test-product',
            category=self.category,
            price=Decimal('100.00'),
            stock=10,
            user=self.user,
            weight=1.0,
            length=1.0,
            width=1.0,
            height=1.0
        )

        # Create a coupon
        self.coupon = Coupon.objects.create(
            code='TESTCODE',
            discount=20,  # 20% discount
            active=True,
            valid_from=timezone.now(),
            valid_to=timezone.now() + timedelta(days=1)
        )

        # Create an address
        self.address = Address.objects.create(
            user=self.user,
            province='Tehran',
            city='Tehran',
            postal_code='1234567890',
            full_address='Azadi St.',
            receiver_name='Test User',
            receiver_phone='09123456789'
        )

    def test_add_to_cart_apply_coupon_create_order(self):
        """
        Test the full workflow:
        1. Add a product to the cart.
        2. Apply a valid coupon.
        3. Create an order.
        4. Verify the order details and stock reduction.
        """
        # Authenticate the user
        self.client.force_authenticate(user=self.user)

        # 1. Add product to cart
        add_to_cart_url = reverse('api-v1:cart-add', kwargs={'product_id': self.product.product_id})
        response = self.client.post(add_to_cart_url, {'quantity': 2, 'override': True}, format='json')
        print(response.content)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.client.session['cart'][str(self.product.product_id)]['quantity'], 2)

        # 2. Apply coupon
        apply_coupon_url = reverse('api-v1:coupon-apply-coupon')
        response = self.client.post(apply_coupon_url, {'code': self.coupon.code}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.client.session.get('coupon_id'), self.coupon.id)

        # 3. Create order
        create_order_url = reverse('api-v1:order-list')
        order_data = {'address_id': self.address.id}
        response = self.client.post(create_order_url, order_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # 4. Verify the order
        self.assertEqual(response.data['user'], self.user.get_full_name())
        self.assertEqual(response.data['coupon'], self.coupon.code)

        # Check subtotal (2 * 100)
        self.assertEqual(Decimal(response.data['subtotal']), Decimal('200.00'))

        # Check discount (20% of 200)
        self.assertEqual(Decimal(response.data['discount_amount']), Decimal('40.00'))

        # Check total payable
        # subtotal - discount + shipping + tax
        # (200 - 40) + 15 (shipping) + (200 * 0.09) (tax) = 160 + 15 + 18 = 193
        expected_total = Decimal('193.00')
        self.assertEqual(Decimal(response.data['total_payable']), expected_total)

        # Verify stock reduction
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 8)

        # Verify cart is cleared
        self.assertNotIn('cart', self.client.session)
