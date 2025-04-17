import decimal
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from cart.cart import Cart
from shop.models import Product, Category

User = get_user_model()


class CartTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.category = Category.objects.create(name='Test Category')
        self.product = Product.objects.create(
            user=self.user,
            name='Test Product',
            price=decimal.Decimal('10.00'),
            stock=100,
            category=self.category
        )
        self.cart_session_id = self.client.session.get('cart', {})

    def test_add_product_to_cart(self):
        cart = Cart(self.client)
        cart.add(self.product, quantity=2)
        self.assertEqual(len(cart), 2)
        self.assertIn(str(self.product.product_id), cart.cart)

    def test_remove_product_from_cart(self):
        cart = Cart(self.client)
        cart.add(self.product, quantity=2)
        cart.remove(self.product)
        self.assertNotIn(str(self.product.product_id), cart.cart)

    def test_clear_cart(self):
        cart = Cart(self.client)
        cart.add(self.product, quantity=2)
        cart.clear()
        cart = Cart(self.client)  # Reinitialize the cart to reflect the cleared session
        self.assertEqual(len(cart), 0)

    def test_get_total_price(self):
        cart = Cart(self.client)
        cart.add(self.product, quantity=2)
        self.assertEqual(cart.get_total_price(), decimal.Decimal('20.00'))


class CartAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.category = Category.objects.create(name='Test Category')
        self.product = Product.objects.create(
            user=self.user,
            name='Test Product',
            price=Decimal('10.00'),
            stock=100,
            category=self.category
        )
        self.cart_url = reverse('api-v1:cart')
        self.client.login(username='testuser', password='testpass')

    def test_get_cart(self):
        response = self.client.get(self.cart_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('items', response.data)
        self.assertIn('total_price', response.data)

    def test_add_product_to_cart(self):
        response = self.client.post(
            reverse('api-v1:cart-product', kwargs={'product_id': self.product.product_id}),
            data={'quantity': 2}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], 'Product added/updated in cart')

    def test_remove_product_from_cart(self):
        self.client.post(
            reverse('api-v1:cart-product', kwargs={'product_id': self.product.product_id}),
            data={'quantity': 2}
        )
        response = self.client.delete(reverse('api-v1:cart-product', kwargs={'product_id': self.product.product_id}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], 'Product removed from cart')
