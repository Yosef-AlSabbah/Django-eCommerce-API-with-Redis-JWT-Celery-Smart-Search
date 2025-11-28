import json
from asgiref.sync import sync_to_async
from channels.testing import WebsocketCommunicator
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from shop.models import Product, Category
from .models import Message
from ecommerce_api.asgi import application

class MessageModelTest(TestCase):
    def setUp(self):
        self.sender = get_user_model().objects.create_user(
            username='sender',
            email='sender@example.com',
            password='password'
        )
        self.recipient = get_user_model().objects.create_user(
            username='recipient',
            email='recipient@example.com',
            password='password'
        )
        self.category = Category.objects.create(name='Test Category')
        self.product = Product.objects.create(
            name='Test Product',
            user=self.recipient,
            category=self.category,
            price=10.00,
            stock=1,
            description='Test Description',
            weight=1.0,
            length=1.0,
            width=1.0,
            height=1.0,
        )

    def test_create_message(self):
        message = Message.objects.create(
            sender=self.sender,
            recipient=self.recipient,
            product=self.product,
            content='This is a test message.'
        )
        self.assertEqual(Message.objects.count(), 1)
        self.assertEqual(message.sender, self.sender)
        self.assertEqual(message.recipient, self.recipient)
        self.assertEqual(message.product, self.product)
        self.assertEqual(message.content, 'This is a test message.')
        self.assertIsNotNone(message.sent_at)


class ProductChatAPIViewTest(TestCase):
    def setUp(self):
        self.user1 = get_user_model().objects.create_user(username='user1', email='user1@test.com', password='password')
        self.user2 = get_user_model().objects.create_user(username='user2', email='user2@test.com', password='password')
        self.category = Category.objects.create(name='Test Category')
        self.product = Product.objects.create(
            name='Test Product',
            user=self.user2,
            category=self.category,
            price=100.0,
            stock=10,
            weight=1.0,
            length=1.0,
            width=1.0,
            height=1.0,
        )
        self.client = APIClient()

        # Create some messages for the product
        for i in range(15):
            Message.objects.create(
                sender=self.user1,
                recipient=self.user2,
                product=self.product,
                content=f'Message {i}'
            )

    def test_get_product_chat_messages_authenticated(self):
        self.client.force_authenticate(user=self.user1)
        url = reverse('api-v1:chat', kwargs={'product_id': self.product.product_id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['data']['messages']), 10)

    def test_get_product_chat_messages_unauthenticated(self):
        url = reverse('api-v1:chat', kwargs={'product_id': self.product.product_id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)

    def test_get_product_chat_messages_product_not_found(self):
        self.client.force_authenticate(user=self.user1)
        import uuid
        non_existent_uuid = uuid.uuid4()
        url = reverse('api-v1:chat', kwargs={'product_id': non_existent_uuid})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_pagination(self):
        self.client.force_authenticate(user=self.user1)
        url = reverse('api-v1:chat', kwargs={'product_id': self.product.product_id})
        response = self.client.get(url, {'page': 2, 'page_size': 5})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['data']['messages']), 5)

class ChatConsumerTest(TestCase):
    async def asyncSetUp(self):
        User = get_user_model()
        self.user1 = await sync_to_async(User.objects.create_user)(username='user1', email='user1@test.com', password='password')
        self.user2 = await sync_to_async(User.objects.create_user)(username='user2', email='user2@test.com', password='password')
        self.category = await Category.objects.acreate(name='Test Category')
        self.product = await Product.objects.acreate(
            name='Test Product',
            user=self.user2,
            category=self.category,
            price=100.0,
            stock=10,
            weight=1.0,
            length=1.0,
            width=1.0,
            height=1.0,
        )

    async def test_connect_authenticated(self):
        await self.asyncSetUp()
        communicator = WebsocketCommunicator(application, f"/ws/chat/room/{self.product.product_id}/")
        communicator.scope['user'] = self.user1
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        await communicator.disconnect()

    async def test_connect_unauthenticated(self):
        from django.contrib.auth.models import AnonymousUser
        await self.asyncSetUp()
        communicator = WebsocketCommunicator(application, f"/ws/chat/room/{self.product.product_id}/")
        communicator.scope['user'] = AnonymousUser()
        connected, _ = await communicator.connect()
        self.assertFalse(connected)

    async def test_receive_message(self):
        await self.asyncSetUp()
        communicator = WebsocketCommunicator(application, f"/ws/chat/room/{self.product.product_id}/")
        communicator.scope['user'] = self.user1
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        await communicator.send_to(text_data=json.dumps({
            'message': 'Hello, world!'
        }))

        # First, receive the confirmation message
        confirmation = await communicator.receive_from()
        confirmation_data = json.loads(confirmation)
        self.assertEqual(confirmation_data['type'], 'message_sent')

        # Then, receive the broadcasted message
        response = await communicator.receive_from()
        response_data = json.loads(response)
        self.assertEqual(response_data['sender'], self.user1.username)
        self.assertEqual(response_data['message'], 'Hello, world!')

        await communicator.disconnect()

    async def test_receive_message_seller_to_buyer(self):
        await self.asyncSetUp()
        communicator = WebsocketCommunicator(application, f"/ws/chat/room/{self.product.product_id}/")
        communicator.scope['user'] = self.user2  # Seller
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        await communicator.send_to(text_data=json.dumps({
            'message': 'Hello, buyer!',
            'recipient': self.user1.username
        }))

        # First, receive the confirmation message
        confirmation = await communicator.receive_from()
        confirmation_data = json.loads(confirmation)
        self.assertEqual(confirmation_data['type'], 'message_sent')

        # Then, receive the broadcasted message
        response = await communicator.receive_from()
        response_data = json.loads(response)
        self.assertEqual(response_data['sender'], self.user2.username)
        self.assertEqual(response_data['message'], 'Hello, buyer!')

        await communicator.disconnect()
