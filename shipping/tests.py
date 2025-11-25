from unittest.mock import patch, MagicMock
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from orders.models import Order
from account.models import Address
from shop.models import Product, Category
from .providers import PostexShippingProvider

User = get_user_model()


class PostexShippingProviderTests(APITestCase):
    @patch('shipping.providers.requests.post')
    def test_create_shipment_success(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'data': [{'tracking_code': '123', 'id': '456'}]}
        mock_post.return_value = mock_response

        user = User.objects.create_user(email='test@example.com', password='password')
        address = Address.objects.create(user=user, city='Tehran', province='Tehran', full_address='123 Main St', postal_code='12345')
        order = Order.objects.create(user=user, address=address)

        provider = PostexShippingProvider()
        result = provider.create_shipment(order)
        self.assertEqual(result['data'][0]['tracking_code'], '123')

    @patch('shipping.providers.requests.get')
    def test_get_cities_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'data': [{'name': 'Tehran', 'code': 1}]}
        mock_get.return_value = mock_response

        provider = PostexShippingProvider()
        result = provider.get_cities()
        self.assertEqual(result['data'][0]['name'], 'Tehran')


class ShippingViewTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='test@example.com', password='password')
        self.category = Category.objects.create(name='Test Category')
        self.product = Product.objects.create(
            name='Test Product', category=self.category, price=100, stock=10, user=self.user,
            weight=1, length=1, width=1, height=1
        )
        self.address = Address.objects.create(user=self.user, city='Tehran', province='Tehran', full_address='123 Main St', postal_code='12345', city_code=1)
        self.order = Order.objects.create(user=self.user, address=self.address)
        self.order.items.create(product=self.product, quantity=1)

    @patch('shipping.providers.PostexShippingProvider.get_cities')
    def test_city_list_view(self, mock_get_cities):
        mock_get_cities.return_value = {'data': [{'name': 'Tehran', 'code': 1}]}
        url = reverse('shipping:city-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data'][0]['name'], 'Tehran')

    @patch('shipping.providers.PostexShippingProvider.get_shipping_quote')
    def test_calculate_shipping_cost_view(self, mock_get_quote):
        mock_get_quote.return_value = {'data': [{'price': 5000}]}
        url = reverse('shipping:calculate-cost')
        data = {'order_id': self.order.order_id}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['shipping_cost'], 5000)
        self.order.refresh_from_db()
        self.assertEqual(self.order.shipping_cost, 5000)
