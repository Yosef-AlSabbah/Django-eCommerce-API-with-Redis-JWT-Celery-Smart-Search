from django.urls import path

from payment.views import PaymentProcessAPIView, PaymentCompletedAPIView, PaymentCanceledAPIView
from payment.webhooks import stripe_webhook

app_name = 'payment'

urlpatterns = [
    path('process/', PaymentProcessAPIView.as_view(), name='process'),
    path('completed/', PaymentCompletedAPIView.as_view(), name='completed'),
    path('canceled/', PaymentCanceledAPIView.as_view(), name='canceled'),
    path('webhook/', stripe_webhook, name='stripe-webhook'),
]
