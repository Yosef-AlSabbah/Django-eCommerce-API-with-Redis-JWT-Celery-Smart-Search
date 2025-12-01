from .base import *

DEBUG = False

ADMINS = [
    ('Yousef Y', 'hypexstore@gmail.com'),
]

ALLOWED_HOSTS = ['eCommerce.com', 'www.eCommerce.com', 'web']

CORS_ALLOWED_ORIGINS = [
    "https://your-frontend-domain.com",
]

REDIS_URL = 'redis://cache:6379'
CACHES['default']['LOCATION'] = REDIS_URL
# CHANNEL_LAYERS['default']['CONFIG']['hosts'] = [REDIS_URL]
