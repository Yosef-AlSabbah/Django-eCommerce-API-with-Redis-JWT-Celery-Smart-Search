from unittest.mock import patch, MagicMock
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from orders.models import Order
from .gateways import ZibalGateway
from decimal import Decimal

User = get_user_model()


class ZibalGatewayTests(APITestCase):
    @patch('payment.gateways.requests.post')
    def test_create_payment_request_success(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'result': 100, 'trackId': '12345'}
        mock_post.return_value = mock_response

        gateway = ZibalGateway()
        result = gateway.create_payment_request(1000, 'test-order', 'http://localhost/callback')
        self.assertEqual(result['result'], 100)
        self.assertEqual(result['trackId'], '12345')

    @patch('payment.gateways.requests.post')
    def test_verify_payment_success(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'result': 100, 'refNumber': '54321'}
        mock_post.return_value = mock_response

        gateway = ZibalGateway()
        result = gateway.verify_payment('12345')
        self.assertEqual(result['result'], 100)
        self.assertEqual(result['refNumber'], '54321')


class PaymentViewTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='test@example.com', password='password')
        self.order = Order.objects.create(user=self.user, total_payable=Decimal('150.00'))

    @patch('payment.gateways.ZibalGateway.create_payment_request')
    def test_payment_request_view(self, mock_create_request):
        mock_create_request.return_value = {'result': 100, 'trackId': '12345'}
        url = reverse('payment:process', kwargs={'order_id': self.order.order_id})
        self.client.force_authenticate(user=self.user)
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('payment_url', response.data)
        self.order.refresh_from_db()
        self.assertEqual(self.order.payment_track_id, '12345')

    @patch('payment.views.create_postex_shipment_task.delay')
    @patch('payment.gateways.ZibalGateway.verify_payment')
    def test_payment_verify_view_success(self, mock_verify, mock_delay):
        self.order.payment_track_id = '12345'
        self.order.save()
        mock_verify.return_value = {'result': 100, 'refNumber': '54321'}
        url = reverse('payment:verify')
        response = self.client.get(url, {'trackId': '12345'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.order.refresh_from_db()
        self.assertEqual(self.order.payment_status, Order.PaymentStatus.SUCCESS)
        self.assertEqual(self.order.payment_ref_id, '54321')
        mock_delay.assert_called_once_with(self.order.order_id)

    @patch('payment.gateways.ZibalGateway.verify_payment')
    def test_payment_verify_view_failure(self, mock_verify):
        self.order.payment_track_id = '12345'
        self.order.save()
        mock_verify.return_value = {'result': 101} # An unsuccessful result code
        url = reverse('payment:verify')
        response = self.client.get(url, {'trackId': '12345'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.order.refresh_from_db()
        self.assertEqual(self.order.payment_status, Order.PaymentStatus.FAILED)
