"""
ASGI config for ecommerce_api project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

from chat.routing import websocket_urlpatterns as chat_ws
from shop.routing import websocket_urlpatterns as search_ws

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_api.settings')

django_asgi_application = get_asgi_application()

websocket_urlpatterns = chat_ws + search_ws

application = ProtocolTypeRouter({
    'http': django_asgi_application,
    'websocket': AuthMiddlewareStack(
        URLRouter(
            websocket_urlpatterns,
        )
    )
})
