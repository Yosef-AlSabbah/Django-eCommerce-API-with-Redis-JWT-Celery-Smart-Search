from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from orders.models import Order, OrderItem
from shop.models import Product, Category

User = get_user_model()


class PaymentViewsTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='testpassword')
        self.category = Category.objects.create(name='Test Category')
        self.product = Product.objects.create(
            name='Test Product',
            category=self.category,
            user=self.user,
            stock=10,
            price=100,
            weight=1,
            length=1,
            width=1,
            height=1
        )
        self.order = Order.objects.create(user=self.user, total_payable=100)
        self.order_item = OrderItem.objects.create(order=self.order, product=self.product, quantity=1)
        self.client.force_authenticate(user=self.user)

    @patch('payment.gateways.ZibalGateway.create_payment_request')
    def test_successful_payment_request(self, mock_create_payment_request):
        mock_create_payment_request.return_value = {'result': 100, 'trackId': '12345'}
        url = reverse('payment:process', kwargs={'order_id': self.order.order_id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('payment_url', response.data['data'])
        self.order.refresh_from_db()
        self.assertEqual(self.order.payment_track_id, '12345')

    def test_already_paid_order(self):
        self.order.payment_status = Order.PaymentStatus.SUCCESS
        self.order.save()
        url = reverse('payment:process', kwargs={'order_id': self.order.order_id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['message'], 'This order has already been paid.')

    def test_insufficient_stock(self):
        self.product.stock = 0
        self.product.save()
        url = reverse('payment:process', kwargs={'order_id': self.order.order_id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Insufficient stock', response.data['message'])

    @patch('payment.gateways.ZibalGateway.create_payment_request')
    def test_gateway_failure(self, mock_create_payment_request):
        mock_create_payment_request.return_value = {'result': 101}
        url = reverse('payment:process', kwargs={'order_id': self.order.order_id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['message'], 'Failed to create payment request.')

    @patch('payment.gateways.ZibalGateway.verify_payment')
    @patch('shipping.tasks.create_postex_shipment_task.delay')
    def test_successful_payment_verification(self, mock_create_shipment, mock_verify_payment):
        self.order.payment_track_id = '12345'
        self.order.save()
        mock_verify_payment.return_value = {'result': 100, 'refNumber': '54321'}
        url = reverse('payment:verify') + '?trackId=12345'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.order.refresh_from_db()
        self.assertEqual(self.order.payment_status, Order.PaymentStatus.SUCCESS)
        self.assertEqual(self.order.payment_ref_id, '54321')
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 9)
        mock_create_shipment.assert_called_once_with(self.order.order_id)

    def test_invalid_track_id(self):
        url = reverse('payment:verify') + '?trackId=invalid'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch('payment.gateways.ZibalGateway.verify_payment')
    def test_gateway_verification_failure(self, mock_verify_payment):
        self.order.payment_track_id = '12345'
        self.order.save()
        mock_verify_payment.return_value = {'result': 101}
        url = reverse('payment:verify') + '?trackId=12345'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.order.refresh_from_db()
        self.assertEqual(self.order.payment_status, Order.PaymentStatus.FAILED)

    @patch('payment.gateways.ZibalGateway.verify_payment')
    def test_insufficient_stock_after_payment(self, mock_verify_payment):
        self.order.payment_track_id = '12345'
        self.order.save()
        mock_verify_payment.return_value = {'result': 100}
        self.product.stock = 0
        self.product.save()
        url = reverse('payment:verify') + '?trackId=12345'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.order.refresh_from_db()
        self.assertEqual(self.order.payment_status, Order.PaymentStatus.FAILED)
