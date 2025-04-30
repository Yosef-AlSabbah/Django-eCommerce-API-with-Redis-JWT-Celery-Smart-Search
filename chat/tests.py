from channels.testing import WebsocketCommunicator
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from chat.consumers import ChatConsumer
from chat.models import Message
from shop.models import Product, Category

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


class ChatConsumerTest(TestCase):
    def setUp(self):
        # Create test users
        self.User = get_user_model()
        self.seller = self.User.objects.create_user(username='seller', password='password', email='1@d.com')
        self.buyer = self.User.objects.create_user(username='buyer', password='password', email='2@d.com')

        # Create a test product
        self.category = Category.objects.create(name='TestCat', slug='testcat')
        self.product = Product.objects.create(name='Test Product', user=self.seller, price=10.00, stock=5, category=self.category)

    async def test_chat_consumer(self):
        # Simulate WebSocket connection for the buyer
        communicator = WebsocketCommunicator(
            ChatConsumer.as_asgi(),
            f'/ws/chat/{self.product.product_id}/'
        )
        communicator.scope['user'] = self.buyer
        communicator.scope['url_route'] = {'kwargs': {'product_id': self.product.product_id}}

        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        # Send a message from the buyer
        message = 'Hello, I am interested in your product!'
        await communicator.send_json_to({
            'message': message
        })

        # Receive the message from the WebSocket
        response = await communicator.receive_json_from()
        self.assertEqual(response['message'], message)
        self.assertEqual(response['sender'], self.buyer.username)

        # Check if the message was saved in the database
        saved_message = Message.objects.get(content=message)
        self.assertEqual(saved_message.sender, self.buyer)
        self.assertEqual(saved_message.recipient, self.seller)
        self.assertEqual(saved_message.product, self.product)

        # Disconnect the WebSocket
        await communicator.disconnect()

