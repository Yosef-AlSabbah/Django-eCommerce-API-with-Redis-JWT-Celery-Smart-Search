from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import Address

User = get_user_model()


class AddressModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='test@example.com', password='testpassword')

    def test_address_creation(self):
        address = Address.objects.create(
            user=self.user,
            province='Tehran',
            city='Tehran',
            postal_code='1234567890',
            full_address='123 Main St',
            receiver_name='Test User',
            receiver_phone='09123456789'
        )
        self.assertEqual(str(address), '123 Main St, Tehran, Tehran')
        self.assertEqual(Address.objects.count(), 1)
