import datetime
import decimal
from unittest.mock import patch

from django.conf import settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from coupons.models import Coupon
from orders.models import Order, OrderItem
from shop.models import Product, Category

User = get_user_model()


class OrderAPITests(APITestCase):

    def setUp(self):
        self.admin = User.objects.create_superuser(
            username='admin', password='pass', email='admin@example.com'
        )
        self.user = User.objects.create_user(username='user', password='pass', email='1@1.com')
        self.category = Category.objects.create(name='Test Category')
        self.product1 = Product.objects.create(
            user=self.admin,
            name='Test Product 1', price=50.00, stock=100, category=self.category
        )
        self.product2 = Product.objects.create(
            user=self.admin,
            name='Test Product 2', price=30.00, stock=50, category=self.category,
        )
        self.coupon = Coupon.objects.create(
            code='TEST10',
            discount=10,
            active=True,
            valid_from=timezone.make_aware(datetime.datetime(2025, 1, 1)),
            valid_to=timezone.make_aware(datetime.datetime(2025, 12, 31)),
        )
        self.url = reverse('api-v1:order-list')
        self.cart_session_id = getattr(settings, 'CART_SESSION_ID', 'cart')

        # Set JWT token for admin by default
        refresh = RefreshToken.for_user(self.admin)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')

    def prepare_cart_session(self, products):
        session = self.client.session
        session[self.cart_session_id] = {}
        for product, quantity in products:
            product_id_str = str(product.product_id)
            session[self.cart_session_id][product_id_str] = {
                'quantity': quantity,
                'price': str(product.price)
            }
        session.save()

    def test_create_order_empty_cart(self):
        refresh = RefreshToken.for_user(self.admin)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')
        session = self.client.session
        if self.cart_session_id in session:
            del session[self.cart_session_id]
        session.save()

        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], "You cannot place an order with an empty cart.")

    def test_create_order_with_cart(self):
        refresh = RefreshToken.for_user(self.admin)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')
        self.prepare_cart_session([(self.product1, 2)])

        with patch('orders.views.send_order_confirmation_email.delay') as mock_task:
            response = self.client.post(self.url)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        order = Order.objects.get(order_id=response.data['order_id'])
        self.assertEqual(order.user, self.admin)
        self.assertEqual(order.items.count(), 1)
        order_item = order.items.first()
        self.assertEqual(order_item.product, self.product1)
        self.assertEqual(order_item.quantity, 2)
        self.assertEqual(order_item.price, decimal.Decimal('100.00'))
        mock_task.assert_called_once_with(order.order_id)

    def test_create_order_with_multiple_products(self):
        refresh = RefreshToken.for_user(self.admin)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')
        self.prepare_cart_session([(self.product1, 1), (self.product2, 3)])

        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        order = Order.objects.get(order_id=response.data['order_id'])
        self.assertEqual(order.items.count(), 2)
        self.assertEqual(order.quantity, 4)
        self.assertEqual(order.get_total_cost_before_discount(), decimal.Decimal('140.00'))

    def test_order_list_filtered_by_user(self):
        order1 = Order.objects.create(user=self.admin, quantity=1)
        OrderItem.objects.create(order=order1, product=self.product1, quantity=1)

        order2 = Order.objects.create(user=self.user, quantity=1)
        OrderItem.objects.create(order=order2, product=self.product2, quantity=1)

        # Admin can see all orders
        refresh = RefreshToken.for_user(self.admin)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']), 2)

        # Regular user can only see their own orders
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']), 1)
        self.assertEqual(response.data['data'][0]['order_id'], str(order2.order_id))

    def test_order_retrieve(self):
        order = Order.objects.create(user=self.admin, quantity=1)
        OrderItem.objects.create(order=order, product=self.product1, quantity=2)
        detail_url = reverse('api-v1:order-detail', kwargs={'pk': order.order_id})

        # Admin can retrieve any order
        refresh = RefreshToken.for_user(self.admin)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['order_id'], str(order.order_id))

        # Regular user cannot retrieve other user's order
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_order_update_permissions(self):
        order = Order.objects.create(user=self.admin, quantity=1)
        OrderItem.objects.create(order=order, product=self.product1, quantity=1)
        detail_url = reverse('api-v1:order-detail', kwargs={'pk': order.order_id})
        data = {'status': 'CO'}

        # Regular user cannot update
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')
        response = self.client.patch(detail_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Admin can update
        refresh = RefreshToken.for_user(self.admin)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')
        response = self.client.patch(detail_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        order.refresh_from_db()
        self.assertEqual(order.status, 'CO')

    def test_order_delete_permissions(self):
        order = Order.objects.create(user=self.admin, quantity=1)
        OrderItem.objects.create(order=order, product=self.product1, quantity=1)
        detail_url = reverse('api-v1:order-detail', kwargs={'pk': order.order_id})

        # Regular user cannot delete
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')
        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Admin can delete
        refresh = RefreshToken.for_user(self.admin)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')
        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Order.objects.filter(pk=order.order_id).exists())

    def test_order_serializer_fields(self):
        order = Order.objects.create(user=self.admin, quantity=1, coupon=self.coupon)
        OrderItem.objects.create(order=order, product=self.product1, quantity=2)
        detail_url = reverse('api-v1:order-detail', kwargs={'pk': order.order_id})

        refresh = RefreshToken.for_user(self.admin)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')
        response = self.client.get(detail_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data
        self.assertIn('order_id', data)
        self.assertIn('user', data)
        self.assertIn('quantity', data)
        self.assertIn('order_date', data)
        self.assertIn('order_items', data)
        self.assertIn('original_price', data)
        self.assertEqual(data['original_price'], '100.00')
        self.assertIn('total_price', data)
        self.assertEqual(data['total_price'], '90.00')
        self.assertIn('coupon', data)
        self.assertEqual(data['coupon'], 'TEST10')
        self.assertIn('discount', data)
        self.assertEqual(data['discount'], '10.00')

    def test_order_status_choices(self):
        order = Order.objects.create(user=self.admin, quantity=1)
        detail_url = reverse('api-v1:order-detail', kwargs={'pk': order.order_id})

        refresh = RefreshToken.for_user(self.admin)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')
        response = self.client.get(detail_url)
        self.assertEqual(response.data['status'], 'PE')

        # Valid status update
        data = {'status': 'CO'}
        response = self.client.patch(detail_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'CO')

        # Invalid status
        data = {'status': 'INVALID'}
        response = self.client.patch(detail_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unauthenticated_access(self):
        self.client.credentials()  # Remove authentication

        # List
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Create
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Retrieve
        order = Order.objects.create(user=self.admin, quantity=1)
        detail_url = reverse('api-v1:order-detail', kwargs={'pk': order.order_id})
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
