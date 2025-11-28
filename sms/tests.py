from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from .models import OTPCode
from rest_framework.test import APITestCase
from unittest.mock import patch
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()


class OTPCodeModelTest(TestCase):
    def test_is_expired(self):
        # Create an expired OTP
        expired_otp = OTPCode.objects.create(
            phone="1234567890",
            code="123456",
            expires_at=timezone.now() - timedelta(minutes=1)
        )
        self.assertTrue(expired_otp.is_expired())

        # Create a non-expired OTP
        non_expired_otp = OTPCode.objects.create(
            phone="1234567890",
            code="654321",
            expires_at=timezone.now() + timedelta(minutes=1)
        )
        self.assertFalse(non_expired_otp.is_expired())


class RequestOTPTest(APITestCase):
    @patch('sms.views.SmsIrProvider.send_otp')
    def test_request_otp_success(self, mock_send_otp):
        mock_send_otp.return_value = {'status': 'ok'}
        url = reverse('sms:request-otp')
        data = {'phone': '1234567890'}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['message'], 'OTP sent successfully')
        self.assertTrue(response.data['success'])
        self.assertTrue(OTPCode.objects.filter(phone='1234567890').exists())

    def test_request_otp_no_phone(self):
        url = reverse('sms:request-otp')
        data = {}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['message'], 'Phone number is required')
        self.assertFalse(response.data['success'])


class VerifyOTPTest(APITestCase):
    def setUp(self):
        self.phone = '1234567890'
        self.code = '123456'
        self.otp = OTPCode.objects.create(
            phone=self.phone,
            code=self.code,
            expires_at=timezone.now() + timedelta(minutes=5)
        )
        self.url = reverse('sms:verify-otp')

    def test_verify_otp_success(self):
        data = {'phone': self.phone, 'code': self.code}
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['message'], 'OTP verified successfully')
        self.assertTrue(response.data['success'])
        self.assertIn('access', response.data['data'])
        self.assertIn('refresh', response.data['data'])
        self.otp.refresh_from_db()
        self.assertTrue(self.otp.used)

    def test_verify_otp_invalid_code(self):
        data = {'phone': self.phone, 'code': '654321'}
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['message'], 'Invalid or expired OTP')
        self.assertFalse(response.data['success'])

    def test_verify_otp_expired_code(self):
        self.otp.expires_at = timezone.now() - timedelta(minutes=1)
        self.otp.save()
        data = {'phone': self.phone, 'code': self.code}
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['message'], 'Invalid or expired OTP')
        self.assertFalse(response.data['success'])
