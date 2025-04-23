import stripe
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from orders.models import Order


@csrf_exempt
def stripe_webhook(request):
    """
    Handle Stripe webhook events.

    This view processes incoming webhook events from Stripe, verifies their
    signatures, and updates the order status in the database when a payment
    is successfully completed.

    Args:
        request (HttpRequest): The HTTP request object containing the webhook payload.

    Returns:
        HttpResponse: A response with the appropriate HTTP status code.
    """

    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        # Invalid payload
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return HttpResponse(status=400)
    if event.type == 'checkout.session.completed':
        session = event.data.object
        if (
                session.mode == 'payment'
                and session.payment_status == 'paid'
        ):
            try:
                order = Order.objects.get(
                    order_id=session.client_reference_id
                )
            except Order.DoesNotExist:
                return HttpResponse(status=404)
            # mark order as paid
            order.status = Order.Status.COMPLETED
            order.stripe_id = session.payment_intent
            order.save()
    return HttpResponse(status=200)
