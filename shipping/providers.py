import requests
from abc import ABC, abstractmethod
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class ShippingProvider(ABC):
    @abstractmethod
    def create_shipment(self, order):
        pass

    @abstractmethod
    def get_shipment_tracking(self, tracking_code):
        pass

    @abstractmethod
    def cancel_shipment(self, tracking_code):
        pass


class PostexShippingProvider(ShippingProvider):
    def __init__(self):
        self.api_key = getattr(settings, 'POSTEX_API_KEY', None)
        self.api_url = 'https://api.postex.ir/api'

    def _get_headers(self):
        return {
            'Content-Type': 'application/json',
            'x-api-key': self.api_key,
        }

    def create_shipment(self, order):
        parcels = [{
            "to": {
                "contact": {
                    "name": order.address.receiver_name,
                    "mobile": order.address.receiver_phone,
                },
                "location": {
                    "address": order.address.full_address,
                    "city_code": order.address.city_code,
                    "postal_code": order.address.postal_code,
                }
            },
            "parcel_items": [{"name": item.product.name, "count": item.quantity} for item in order.items.all()],
            "parcel_properties": {
                "total_weight": int(sum(item.product.weight * item.quantity for item in order.items.all())),
                "total_value": int(order.total_payable),
            }
        }]
        data = {
            "collection_type": "pick_up",
            "parcels": parcels
        }
        logger.info(f"Creating Postex shipment for order {order.order_id}: {data}")
        try:
            response = requests.post(f'{self.api_url}/v1/parcels/bulk', json=data, headers=self._get_headers())
            response.raise_for_status()
            logger.info(f"Postex shipment response for order {order.order_id}: {response.json()}")
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error creating Postex shipment for order {order.order_id}: {e}")
            return {'error': str(e)}

    def get_shipment_tracking(self, tracking_code):
        logger.info(f"Getting Postex shipment tracking for tracking_code {tracking_code}")
        try:
            # The documentation is a bit ambiguous here, assuming courier is 'postex'
            response = requests.get(f'{self.api_url}/v1/tracking/events/postex/{tracking_code}', headers=self._get_headers())
            response.raise_for_status()
            logger.info(f"Postex shipment tracking response for tracking_code {tracking_code}: {response.json()}")
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting Postex shipment tracking for tracking_code {tracking_code}: {e}")
            return {'error': str(e)}

    def get_shipping_quote(self, order):
        parcels = [{
            "to_city_code": order.address.city_code,
            "total_weight": int(sum(item.product.weight * item.quantity for item in order.items.all())),
            "total_value": int(order.total_payable),
        }]
        data = {
            "collection_type": "pick_up",
            "from_city_code": settings.POSTEX_FROM_CITY_CODE,
            "parcels": parcels,
        }
        logger.info(f"Getting Postex shipping quote for order {order.order_id}: {data}")
        try:
            response = requests.post(f'{self.api_url}/v1/shipping/quotes', json=data, headers=self._get_headers())
            response.raise_for_status()
            logger.info(f"Postex shipping quote response for order {order.order_id}: {response.json()}")
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting Postex shipping quote for order {order.order_id}: {e}")
            return {'error': str(e)}

    def cancel_shipment(self, tracking_code):
        logger.info(f"Canceling Postex shipment for tracking_code {tracking_code}")
        try:
            response = requests.delete(f'{self.api_url}/v1/parcels/{tracking_code}', headers=self._get_headers())
            response.raise_for_status()
            logger.info(f"Postex shipment cancellation response for tracking_code {tracking_code}: {response.json()}")
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error canceling Postex shipment for tracking_code {tracking_code}: {e}")
            return {'error': str(e)}

    def get_cities(self):
        logger.info("Getting Postex city list")
        try:
            response = requests.get(f'{self.api_url}/v1/locality/cities/all', headers=self._get_headers())
            response.raise_for_status()
            logger.info("Successfully retrieved Postex city list")
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting Postex city list: {e}")
            return {'error': str(e)}
