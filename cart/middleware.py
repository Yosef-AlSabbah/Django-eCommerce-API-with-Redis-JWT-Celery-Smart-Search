from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse
import json


class CartSessionMiddleware(MiddlewareMixin):
    """
    Middleware to handle cart session for React clients.
    Ensures session is created and cart session ID is properly set.
    """

    def process_request(self, request):
        # Ensure session exists for cart endpoints
        if '/cart/' in request.path:
            if not request.session.session_key:
                request.session.create()
        return None

    def process_response(self, request, response):
        # Add session ID to response headers for React client
        if '/cart/' in request.path and hasattr(request, 'session'):
            if request.session.session_key:
                response['X-Session-ID'] = request.session.session_key
        return response
