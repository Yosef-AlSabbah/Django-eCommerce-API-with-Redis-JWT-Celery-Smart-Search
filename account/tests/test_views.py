from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


class UserViewSetTests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email='testuser@example.com',
            username='testuser',
            password='S@mpleP@ss123',
            is_active=True
        )
        self.client.force_authenticate(user=self.user)

    def test_get_user_profile(self):
        url = reverse('auth:current_user')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['username'], self.user.username)

    def test_update_user_profile(self):
        url = reverse('auth:current_user')
        data = {
            'first_name': 'Updated',
            'last_name': 'User',
            'password': 'NewS@mpleP@ss123'
        }
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Updated')

    def test_delete_user_profile(self):
        url = reverse('auth:current_user')
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(User.objects.filter(pk=self.user.pk).exists())


class AuthenticationTests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='S@mpleP@ss123',
            is_active=True
        )

    def test_user_registration(self):
        url = reverse('auth:register')
        data = {
            'email': 'newuser@example.com',
            'username': 'newuser',
            'password': 'S@mpleP@ss123',
            're_password': 'S@mpleP@ss123'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(email='newuser@example.com').exists())

    def test_token_obtain(self):
        url = reverse('auth:jwt-create')
        data = {'email': self.user.email, 'password': 'S@mpleP@ss123'}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data['data'])
        self.assertIn('refresh', response.data['data'])

    def test_token_refresh(self):
        refresh = RefreshToken.for_user(self.user)
        url = reverse('auth:jwt-refresh')
        data = {'refresh': str(refresh)}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data['data'])

    def test_token_destroy(self):
        refresh = RefreshToken.for_user(self.user)
        url = reverse('auth:jwt-destroy')
        data = {'refresh': str(refresh)}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_205_RESET_CONTENT)
