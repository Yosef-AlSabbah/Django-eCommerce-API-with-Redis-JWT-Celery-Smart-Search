import unittest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient

from shop.models import Product, Category

User = get_user_model()


@unittest.skip("Skipping cart tests temporarily")
class CartTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.category = Category.objects.create(name='Test Category')
        self.product = Product.objects.create(
            name='Test Product',
            category=self.category,
            price=10.00,
            stock=10,
            user=self.user,
            weight=1.0,
            length=1.0,
            width=1.0,
            height=1.0
        )

    def test_add_to_cart(self):
        url = reverse('api-v1:cart-add-to-cart', kwargs={'product_id': self.product.product_id})
        data = {'quantity': 2}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.client.session['cart'][str(self.product.product_id)]['quantity'], 2)

    def test_remove_from_cart(self):
        # Add to cart first
        url = reverse('api-v1:cart-add-to-cart', kwargs={'product_id': self.product.product_id})
        data = {'quantity': 2}
        self.client.post(url, data)

        # Then remove
        url = reverse('api-v1:cart-remove-from-cart', kwargs={'product_id': self.product.product_id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn(str(self.product.product_id), self.client.session['cart'])

    def test_clear_cart(self):
        # Add to cart first
        url = reverse('api-v1:cart-add-to-cart', kwargs={'product_id': self.product.product_id})
        data = {'quantity': 2}
        self.client.post(url, data)

        # Then clear
        url = reverse('api-v1:cart-clear-cart')
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertNotIn('cart', self.client.session)
