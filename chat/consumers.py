import json

from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth import get_user_model
from django.utils import timezone


from .models import Message


class ChatConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for handling private product chats between sellers and buyers."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = None
        self.product = None
        self.room_name = None
        self.room_group_name = None
        self.product_id = None

    async def connect(self):
        """
        Handle WebSocket connection.

        - Authenticates the user
        - Verifies the product exists
        - Creates a unique room group for the seller-buyer-product combination
        - Joins the room group

        Rejects connection if:
        - User is not authenticated
        - Product doesn't exist
        """
        self.user = self.scope['user']
        if not self.user.is_authenticated:
            await self.close()
            return

        self.product_id = self.scope['url_route']['kwargs']['product_id']

        from shop.models import Product  # Import Product here

        try:
            # Use async database operations
            self.product = await Product.objects.select_related('user').aget(product_id=self.product_id)
        except Product.DoesNotExist:
            await self.close()
            return

        # Create a unique room name for the seller-buyer-product combination
        # Sort user IDs to ensure same room name regardless of who connects first
        # Use sync_to_async to safely access the product.user.id
        product_user_id = await sync_to_async(lambda: self.product.user.id)()
        user_ids = sorted([str(self.user.id), str(product_user_id)])
        self.room_name = f'chat_product_{self.product_id}_users_{"_".join(user_ids)}'
        self.room_group_name = f'chat_{self.room_name}'

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        """
        Handle WebSocket disconnection.

        Args:
            close_code: Code indicating why the connection was closed.

        Removes the channel from the room group when the connection closes.
        """
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data=None, bytes_data=None):
        """
        Handle incoming WebSocket messages.

        Args:
            text_data: JSON-encoded string containing:
                - message: The chat message content
                - recipient: Required only when sender is the product seller

        Processes the message by:
        - Validating the message content
        - Determining the correct recipient
        - Broadcasting to the room group
        - Persisting to the database
        :param text_data:
        :param bytes_data:
        """
        try:
            text_data_json = json.loads(text_data)
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'error': 'Invalid JSON format'
            }))
            return

        message = text_data_json.get('message', '').strip()

        if not message:
            await self.send(text_data=json.dumps({
                'error': 'Message content is required'
            }))
            return

        # Add message length validation
        if len(message) > 1000:  # Adjust limit as needed
            await self.send(text_data=json.dumps({
                'error': 'Message too long. Maximum 1000 characters allowed.'
            }))
            return

        now = timezone.now()

        # Determine recipient
        if self.user == self.product.seller:
            # Seller is sending - recipient should be the buyer
            recipient_username = text_data_json.get('recipient')
            if not recipient_username:
                await self.send(text_data=json.dumps({
                    'error': 'Recipient username is required when seller sends message'
                }))
                return
            User = get_user_model()

            try:
                recipient = await sync_to_async(User.objects.get)(username=recipient_username)
            except User.DoesNotExist:
                await self.send(text_data=json.dumps({
                    'error': 'Recipient user not found'
                }))
                return
        else:
            # Buyer is sending - recipient is the seller
            recipient = self.product.seller

        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'sender': self.user.username,
                'datetime': now.isoformat(),
                'message_id': None,  # Will be set after saving to DB
            }
        )

        # Save message to database
        try:
            saved_message = await Message.objects.acreate(
                sender=self.user,
                recipient=recipient,
                product=self.product,
                content=message
            )

            # Send confirmation back to sender with message ID
            await self.send(text_data=json.dumps({
                'type': 'message_sent',
                'message_id': saved_message.id,
                'timestamp': saved_message.sent_at.isoformat()
            }))

        except Exception as e:
            await self.send(text_data=json.dumps({
                'error': 'Failed to save message. Please try again.'
            }))
            return

    async def chat_message(self, event):
        """
        Handle sending chat messages to the WebSocket.

        Args:
            event: Dictionary containing:
                - message: The chat message content
                - sender: Username of the message sender
                - datetime: ISO-formatted timestamp of when message was sent

        Sends the formatted message to the WebSocket connection.
        """
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'sender': event['sender'],
            'datetime': event['datetime'],
        }))
