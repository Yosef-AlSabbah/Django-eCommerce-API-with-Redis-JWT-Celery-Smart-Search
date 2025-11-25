from unittest.mock import patch, MagicMock
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from .models import OTPCode
from .providers import SmsIrProvider
import time
from datetime import timedelta
from django.utils import timezone

User = get_user_model()


class SmsIrProviderTests(APITestCase):
    @patch('sms.providers.requests.post')
    def test_send_otp_success(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'status': 1, 'message': 'Success'}
        mock_post.return_value = mock_response

        provider = SmsIrProvider()
        result = provider.send_otp('1234567890', '1234', 123)
        self.assertEqual(result['status'], 1)

    @patch('sms.providers.requests.post')
    def test_send_otp_failure(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {'status': 0, 'message': 'Failed'}
        mock_post.return_value = mock_response

        provider = SmsIrProvider()
        result = provider.send_otp('1234567890', '1234', 123)
        self.assertEqual(result['status'], 0)


class OTPViewTests(APITestCase):
    def setUp(self):
        self.phone_number = '09123456789'
        self.otp_code = '123456'

    @patch('sms.views.SmsIrProvider.send_otp')
    def test_request_otp_success(self, mock_send_otp):
        mock_send_otp.return_value = {'status': 1}
        url = reverse('sms:request-otp')
        data = {'phone': self.phone_number}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(OTPCode.objects.filter(phone=self.phone_number).exists())

    def test_verify_otp_success_new_user(self):
        OTPCode.objects.create(phone=self.phone_number, code=self.otp_code, expires_at=timezone.now() + timedelta(minutes=5))
        url = reverse('sms:verify-otp')
        data = {'phone': self.phone_number, 'code': self.otp_code}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertTrue(User.objects.filter(phone_number=self.phone_number).exists())

    def test_verify_otp_success_existing_user(self):
        user = User.objects.create_user(email='test@example.com', phone_number=self.phone_number, password='testpassword')
        OTPCode.objects.create(phone=self.phone_number, code=self.otp_code, expires_at=timezone.now() + timedelta(minutes=5))
        url = reverse('sms:verify-otp')
        data = {'phone': self.phone_number, 'code': self.otp_code}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertEqual(User.objects.count(), 1)

    def test_verify_otp_invalid_code(self):
        OTPCode.objects.create(phone=self.phone_number, code=self.otp_code, expires_at=timezone.now() + timedelta(minutes=5))
        url = reverse('sms:verify-otp')
        data = {'phone': self.phone_number, 'code': 'wrongcode'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_verify_otp_expired_code(self):
        otp = OTPCode.objects.create(phone=self.phone_number, code=self.otp_code, expires_at=timezone.now() - timedelta(minutes=10))

        url = reverse('sms:verify-otp')
        data = {'phone': self.phone_number, 'code': self.otp_code}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
