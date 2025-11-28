from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from unittest.mock import patch, MagicMock
from orders.models import Order
from account.models import Address, UserAccount as User


class ShippingAPITests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(email='test@example.com', username='testuser', password='testpassword')
        self.address = Address.objects.create(
            user=self.user,
            receiver_name='Test Receiver',
            receiver_phone='1234567890',
            full_address='123 Test St',
            city_code='1',
            postal_code='12345'
        )
        self.order = Order.objects.create(user=self.user, address=self.address, total_payable=10000)

    @patch('shipping.providers.PostexShippingProvider.get_cities')
    def test_get_city_list_success(self, mock_get_cities):
        mock_response = {'data': [{'id': 1, 'name': 'Tehran'}]}
        mock_get_cities.return_value = mock_response

        url = reverse('shipping:city-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data'], mock_response)
        mock_get_cities.assert_called_once()

    @patch('shipping.providers.PostexShippingProvider.get_cities')
    def test_get_city_list_failure(self, mock_get_cities):
        mock_get_cities.return_value = {'error': 'API Error'}

        url = reverse('shipping:city-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.data['message'], 'Failed to get city list')
        mock_get_cities.assert_called_once()

    @patch('shipping.providers.PostexShippingProvider.get_shipping_quote')
    def test_calculate_shipping_cost_success(self, mock_get_shipping_quote):
        mock_response = {'data': [{'price': 5000}]}
        mock_get_shipping_quote.return_value = mock_response

        url = reverse('shipping:calculate-cost')
        data = {'order_id': self.order.order_id}
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data'], {'shipping_cost': 5000})

        self.order.refresh_from_db()
        self.assertEqual(self.order.shipping_cost, 5000)
        mock_get_shipping_quote.assert_called_once_with(self.order)

    @patch('shipping.providers.PostexShippingProvider.get_shipping_quote')
    def test_calculate_shipping_cost_failure(self, mock_get_shipping_quote):
        mock_get_shipping_quote.return_value = {'error': 'API Error'}

        url = reverse('shipping:calculate-cost')
        data = {'order_id': self.order.order_id}
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.data['message'], 'Failed to get shipping cost')
        mock_get_shipping_quote.assert_called_once_with(self.order)

    def test_calculate_shipping_cost_no_order_id(self):
        url = reverse('shipping:calculate-cost')
        response = self.client.post(url, {})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['message'], 'Order ID is required')

    def test_calculate_shipping_cost_no_address(self):
        self.order.address = None
        self.order.save()

        url = reverse('shipping:calculate-cost')
        data = {'order_id': self.order.order_id}
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['message'], 'Order address is not set')
