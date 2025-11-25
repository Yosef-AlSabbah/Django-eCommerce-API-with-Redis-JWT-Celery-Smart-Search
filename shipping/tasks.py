from celery import shared_task
from .providers import PostexShippingProvider
from orders.models import Order

@shared_task
def create_postex_shipment_task(order_id):
    try:
        order = Order.objects.get(order_id=order_id)
        shipping_provider = PostexShippingProvider()
        shipping_response = shipping_provider.create_shipment(order)
        if not shipping_response.get('error') and shipping_response.get('data'):
            # The bulk endpoint returns a list of parcels, we are sending one
            shipment_data = shipping_response['data'][0]
            order.shipping_provider = 'postex'
            order.shipping_tracking_code = shipment_data.get('tracking_code')
            order.postex_shipment_id = shipment_data.get('id')
            order.status = Order.Status.PROCESSING
            order.save()
    except Order.DoesNotExist:
        # Handle order not found
        pass
