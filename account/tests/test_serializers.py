from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory
from account.serializers import UserProfileSerializer, AddressSerializer
from account.models import Address

User = get_user_model()


class UserProfileSerializerTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email='testuser@example.com',
            username='testuser',
            password='password123'
        )
        self.factory = APIRequestFactory()
        self.request = self.factory.get('/me/')
        self.request.user = self.user

        self.serializer_context = {'request': self.request}
        self.valid_data = {
            'first_name': 'New',
            'last_name': 'Name',
            'phone_number': '+989123456789',
            'password': 'newpassword123'
        }

    def test_user_profile_serializer_valid_data(self):
        serializer = UserProfileSerializer(
            instance=self.user.profile,
            data=self.valid_data,
            context=self.serializer_context
        )
        self.assertTrue(serializer.is_valid(raise_exception=True))

    def test_user_profile_serializer_update(self):
        serializer = UserProfileSerializer(
            instance=self.user.profile,
            data=self.valid_data,
            context=self.serializer_context
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        self.user.refresh_from_db()

        self.assertEqual(self.user.first_name, 'New')
        self.assertEqual(self.user.last_name, 'Name')
        self.assertEqual(self.user.phone_number, '+989123456789')
        self.assertTrue(self.user.check_password('newpassword123'))

    def test_user_profile_serializer_invalid_phone_number(self):
        invalid_data = self.valid_data.copy()
        invalid_data['phone_number'] = '123'
        serializer = UserProfileSerializer(
            instance=self.user.profile,
            data=invalid_data,
            context=self.serializer_context
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn('phone_number', serializer.errors)


class AddressSerializerTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email='testuser@example.com',
            username='testuser',
            password='password123'
        )
        self.valid_data = {
            'province': 'Tehran',
            'city': 'Tehran',
            'postal_code': '1234567890',
            'full_address': 'Main Street',
            'receiver_name': 'Test User',
            'receiver_phone': '+989123456789'
        }

    def test_address_serializer_valid_data(self):
        serializer = AddressSerializer(data=self.valid_data)
        self.assertTrue(serializer.is_valid())

    def test_address_serializer_create(self):
        serializer = AddressSerializer(data=self.valid_data)
        serializer.is_valid(raise_exception=True)
        address = serializer.save(user=self.user)

        self.assertEqual(Address.objects.count(), 1)
        self.assertEqual(address.user, self.user)
        self.assertEqual(address.city, 'Tehran')
