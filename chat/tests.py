from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from chat.models import Message
from shop.models import Product

User = get_user_model()


class ChatAppTests(APITestCase):
    def setUp(self):
        self.seller = User.objects.create_user(username='seller', password='pass', email='seller@example.com')
        self.buyer = User.objects.create_user(username='buyer', password='pass', email='buyer@example.com')

        from shop.models import Category
        self.category = Category.objects.create(name='TestCat', slug='testcat')
        self.product = Product.objects.create(
            name='Test Product',
            slug='test-product',
            price=10,
            stock=5,
            category=self.category,
            user=self.seller
        )
        self.url = reverse('api-v1:chat', kwargs={'product_id': str(self.product.product_id)})

    def authenticate(self, user):
        refresh = RefreshToken.for_user(user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')

    def test_message_creation(self):
        self.authenticate(self.buyer)
        msg = Message.objects.create(
            sender=self.buyer,
            recipient=self.seller,
            product=self.product,
            content='Hello!'
        )
        self.assertEqual(Message.objects.count(), 1)
        self.assertEqual(msg.content, 'Hello!')

    def test_api_get_messages(self):
        self.authenticate(self.buyer)
        Message.objects.create(
            sender=self.buyer,
            recipient=self.seller,
            product=self.product,
            content='Hello!'
        )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('data', response.data)
