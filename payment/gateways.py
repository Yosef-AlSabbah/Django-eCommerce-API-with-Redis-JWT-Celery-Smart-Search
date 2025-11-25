import requests
from abc import ABC, abstractmethod
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class PaymentGateway(ABC):
    @abstractmethod
    def create_payment_request(self, amount, order_id, callback_url):
        pass

    @abstractmethod
    def verify_payment(self, payload_or_authority):
        pass


class ZibalGateway(PaymentGateway):
    def __init__(self):
        self.merchant_id = getattr(settings, 'ZIBAL_MERCHANT_ID', None)
        self.api_url = 'https://gateway.zibal.ir/v1'

    def create_payment_request(self, amount, order_id, callback_url):
        headers = {'Content-Type': 'application/json'}
        data = {
            'merchant': self.merchant_id,
            'amount': amount,
            'orderId': str(order_id),
            'callbackUrl': callback_url,
        }
        logger.info(f"Creating Zibal payment request for order {order_id}: {data}")
        try:
            response = requests.post(f'{self.api_url}/request', json=data, headers=headers)
            response.raise_for_status()
            logger.info(f"Zibal payment request response for order {order_id}: {response.json()}")
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error creating Zibal payment request for order {order_id}: {e}")
            return {'error': str(e)}

    def verify_payment(self, payload_or_authority):
        headers = {'Content-Type': 'application/json'}
        data = {
            'merchant': self.merchant_id,
            'trackId': payload_or_authority,
        }
        logger.info(f"Verifying Zibal payment for trackId {payload_or_authority}: {data}")
        try:
            response = requests.post(f'{self.api_url}/verify', json=data, headers=headers)
            response.raise_for_status()
            logger.info(f"Zibal payment verification response for trackId {payload_or_authority}: {response.json()}")
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error verifying Zibal payment for trackId {payload_or_authority}: {e}")
            return {'error': str(e)}
