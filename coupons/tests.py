from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from .models import Coupon

User = get_user_model()


class CouponTests(TestCase):
    def setUp(self):
        # Create test coupons
        self.valid_coupon = Coupon.objects.create(
            code='VALID20',
            valid_from=timezone.now() - timezone.timedelta(days=1),
            valid_to=timezone.now() + timezone.timedelta(days=1),
            discount=20,
            active=True
        )

        self.expired_coupon = Coupon.objects.create(
            code='EXPIRED10',
            valid_from=timezone.now() - timezone.timedelta(days=2),
            valid_to=timezone.now() - timezone.timedelta(days=1),
            discount=10,
            active=True
        )

        self.inactive_coupon = Coupon.objects.create(
            code='INACTIVE15',
            valid_from=timezone.now() - timezone.timedelta(days=1),
            valid_to=timezone.now() + timezone.timedelta(days=1),
            discount=15,
            active=False
        )

        # Admin user for privileged operations
        self.admin_user = User.objects.create(username='admin', is_staff=True, email='<EMAIL>')
        # Regular user for apply endpoint
        self.regular_user = User.objects.create(username='user', is_staff=False)

        # URLs
        self.list_url = reverse('api-v1:coupon-list')
        self.detail_url = reverse('api-v1:coupon-detail', kwargs={'pk': self.valid_coupon.pk})
        self.apply_url = reverse('api-v1:coupon-apply-coupon')

    def create_user(self, is_staff=False):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        return User.objects.create_user(
            username='admin' if is_staff else 'user',
            password='testpass123',
            is_staff=is_staff
        )

    # Helper methods
    def authenticate(self, user):
        self.client = APIClient()
        self.client.force_authenticate(user=user)

    # List tests
    def test_list_coupons_as_admin(self):
        self.authenticate(self.admin_user)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']), 3)

    def test_list_coupons_as_anonymous(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # Create tests
    def test_create_coupon_as_admin(self):
        self.authenticate(self.admin_user)
        data = {
            'code': 'NEW25',
            'valid_from': timezone.now() - timezone.timedelta(days=1),
            'valid_to': timezone.now() + timezone.timedelta(days=1),
            'discount': 25,
            'active': True
        }
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Coupon.objects.count(), 4)

    def test_create_coupon_invalid_dates(self):
        self.authenticate(self.admin_user)
        data = {
            'code': 'INVALID',
            'valid_from': timezone.now() + timezone.timedelta(days=1),
            'valid_to': timezone.now() - timezone.timedelta(days=1),
            'discount': 10,
            'active': True
        }
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # Update tests
    def test_update_coupon_as_admin(self):
        self.authenticate(self.admin_user)
        data = {
            'code': self.valid_coupon.code,  # Same code
            'valid_from': timezone.now() - timezone.timedelta(days=1),
            'valid_to': timezone.now() + timezone.timedelta(days=2),
            'discount': 30,
            'active': True
        }
        response = self.client.put(self.detail_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.valid_coupon.refresh_from_db()
        self.assertEqual(self.valid_coupon.discount, 30)

    def test_update_coupon_code(self):
        self.authenticate(self.admin_user)
        data = {
            'code': 'NEWCODE',
            'valid_from': timezone.now() - timezone.timedelta(days=1),
            'valid_to': timezone.now() + timezone.timedelta(days=1),
            'discount': 20,
            'active': True
        }
        response = self.client.put(self.detail_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('detail', response.data)
        self.assertEqual(response.data['detail'], 'Coupon code cannot be modified.')

    # Delete tests
    def test_delete_coupon_as_admin(self):
        self.authenticate(self.admin_user)
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.valid_coupon.refresh_from_db()
        self.assertFalse(self.valid_coupon.active)
        self.assertEqual(response.data['detail'], 'Coupon has been marked as inactive.')

    # Apply tests
    def test_apply_valid_coupon(self):
        from orders.models import Order
        order = Order.objects.create(user=self.regular_user, coupon=self.valid_coupon)
        self.assertEqual(order.coupon, self.valid_coupon)

    def test_apply_expired_coupon(self):
        response = self.client.post(self.apply_url, {'code': 'EXPIRED10'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], 'Coupon is not valid at this time.')

    def test_apply_inactive_coupon(self):
        response = self.client.post(self.apply_url, {'code': 'INACTIVE15'})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['detail'], 'Invalid or inactive coupon code.')

    def test_apply_invalid_code(self):
        response = self.client.post(self.apply_url, {'code': 'NONEXISTENT'})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['detail'], 'Invalid or inactive coupon code.')

    def test_apply_missing_code(self):
        response = self.client.post(self.apply_url, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], 'Coupon code is required.')

    # Model tests
    def test_coupon_str(self):
        self.assertEqual(str(self.valid_coupon), 'VALID20')

    def test_coupon_is_valid(self):
        self.assertTrue(self.valid_coupon.is_valid())
        self.assertFalse(self.expired_coupon.is_valid())
        self.assertFalse(self.inactive_coupon.is_valid())

    def test_coupon_clean_method(self):
        invalid_coupon = Coupon(
            code='INVALID',
            valid_from=timezone.now() + timezone.timedelta(days=1),
            valid_to=timezone.now() - timezone.timedelta(days=1),
            discount=10,
            active=True
        )
        from django.core.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            invalid_coupon.clean()
