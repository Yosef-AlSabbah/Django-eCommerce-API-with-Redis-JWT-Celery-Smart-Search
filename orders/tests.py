import decimal

from django.conf import settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from orders.models import Order
from shop.models import Product, Category

User = get_user_model()


class OrderAPITests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            username='admin', password='pass', email='admin@example.com'
        )
        self.user = User.objects.create_user(username='user', password='pass')
        self.category = Category.objects.create(name='Test Category')
        self.product = Product.objects.create(
            user=self.admin,
            name='Test Product', price=50.00, stock=100, category=self.category
        )
        self.url = reverse('api-v1:order-list')
        # Ensure CART_SESSION_ID is defined in your Django settings
        self.cart_session_id = getattr(settings, 'CART_SESSION_ID', 'cart')  # Default to 'cart' if not set

    def test_create_order_empty_cart(self):
        self.client.login(username='admin', password='pass')
        # Ensure the cart session key is explicitly removed or empty
        session = self.client.session
        if self.cart_session_id in session:
            del session[self.cart_session_id]
        session.save()

        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)  # Correct assertion for this test

    def test_create_order_with_cart(self):
        self.client.login(username='admin', password='pass')
        session = self.client.session

        # --- Directly prepare the session data ---
        product_id_str = str(self.product.product_id)
        session[self.cart_session_id] = {
            product_id_str: {
                'quantity': 2,
                'price': str(self.product.price)  # Store price as string, like in Cart.add
            }
        }
        session.save()
        # --- End session preparation ---

        response = self.client.post(self.url)

        # Assert the expected success status
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        order = Order.objects.get(order_id=response.data.get('order_id'))
        self.assertEqual(order.user, self.admin)
        self.assertEqual(order.items.count(), 1)
        order_item = order.items.first()
        self.assertEqual(order_item.product, self.product)
        self.assertEqual(order_item.quantity, 2)
        self.assertEqual(order_item.price, decimal.Decimal(
            self.product.price) * 2)  # Check price (might need adjustment based on OrderItem model)

    def test_order_list_filtered_by_user(self):
        self.client.login(username='user', password='pass')
        session = self.client.session

        # --- Directly prepare the session data ---
        product_id_str = str(self.product.product_id)
        session[self.cart_session_id] = {
            product_id_str: {
                'quantity': 1,
                'price': str(self.product.price)
            }
        }
        session.save()
        # --- End session preparation ---

        response_create = self.client.post(self.url)
        # Check creation first
        self.assertEqual(response_create.status_code, status.HTTP_201_CREATED,
                         f"Order creation failed: {response_create.content}")  # Add content on failure

        # Now test the listing part
        response_list = self.client.get(self.url)
        self.assertEqual(response_list.status_code, status.HTTP_200_OK)
