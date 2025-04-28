from django.conf import settings
from django.db import models


class Message(models.Model):
    # The user who sent the message
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='sent_chat_messages',
        on_delete=models.CASCADE,
    )
    # The user who received the message
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='received_chat_messages',
        on_delete=models.CASCADE,
    )
    # The product associated with the chat message
    product = models.ForeignKey(
        'shop.Product',
        related_name='chat_messages',
        on_delete=models.PROTECT,
    )
    content = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-sent_at']
        verbose_name = 'Chat Message'
        verbose_name_plural = 'Chat Messages'

    def __str__(self):
        return f'{self.sender} to {self.recipient} about {self.product} at {self.sent_at}'
