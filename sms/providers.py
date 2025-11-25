import requests
from abc import ABC, abstractmethod
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class SmsProvider(ABC):
    @abstractmethod
    def send_otp(self, phone, code, template_id):
        pass

    @abstractmethod
    def send_text(self, phone, message):
        pass


class SmsIrProvider(SmsProvider):
    def __init__(self):
        self.api_key = getattr(settings, 'SMS_IR_API_KEY', None)
        self.line_number = getattr(settings, 'SMS_IR_LINE_NUMBER', None)
        self.api_url = 'https://api.sms.ir/v1'

    def _get_headers(self):
        return {
            'Content-Type': 'application/json',
            'X-API-KEY': self.api_key,
        }

    def send_otp(self, phone, code, template_id):
        headers = self._get_headers()
        headers['Accept'] = 'text/plain'
        data = {
            'mobile': phone,
            'templateId': template_id,
            'parameters': [
                {'name': 'CODE', 'value': str(code)},
            ],
        }
        logger.info(f"Sending OTP to {phone} via sms.ir: {data}")
        try:
            response = requests.post(f'{self.api_url}/send/verify', json=data, headers=headers)
            response.raise_for_status()
            logger.info(f"sms.ir OTP response for {phone}: {response.json()}")
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error sending OTP to {phone} via sms.ir: {e}")
            return {'error': str(e)}

    def send_text(self, phone, message):
        data = {
            'lineNumber': self.line_number,
            'messageText': message,
            'mobiles': [phone],
        }
        logger.info(f"Sending text message to {phone} via sms.ir: {data}")
        try:
            response = requests.post(f'{self.api_url}/send/bulk', json=data, headers=self._get_headers())
            response.raise_for_status()
            logger.info(f"sms.ir text message response for {phone}: {response.json()}")
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error sending text message to {phone} via sms.ir: {e}")
            return {'error': str(e)}
