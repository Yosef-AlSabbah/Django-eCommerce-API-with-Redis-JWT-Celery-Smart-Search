from celery import shared_task
from django.core.mail import send_mail

from .models import Order


@shared_task
def send_order_confirmation_email(order_id):
    """
    Task to send an e-mail notification when an order is
    successfully created.
    """
    order = Order.objects.get(id=order_id)
    subject = f'Order nr. {order.id}'
    message = (
        f'Dear {order.user.username},\n\n'
        f'You have successfully placed an order.'
        f'Your order ID is {order.id}.'
    )
    mail_sent = send_mail(
        subject, message, 'admin@eCommerce.com', [order.user.email]
    )
    return mail_sent
