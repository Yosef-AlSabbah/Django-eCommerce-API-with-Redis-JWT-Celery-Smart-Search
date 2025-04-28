import json
import time

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.core.cache import cache

from shop.models import Product
from shop.utils import search_products


class SearchConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for handling real-time product search queries.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(args, kwargs)
        self.throttle_id = None

    async def connect(self):
        """
        Handles the WebSocket connection event.
        Initializes a throttle ID for rate-limiting and accepts the connection.
        """
        self.throttle_id = self.channel_name
        await self.accept()

    async def disconnect(self, close_code):
        """
        Handles the WebSocket disconnection event.
        Removes any cached data related to the throttle ID.
        """
        cache.delete(f"search_suggestions_{self.throttle_id}")
        cache.delete(f"last_query_{self.throttle_id}")
        cache.delete(f"throttle_ws_{self.throttle_id}")

    async def receive(self, text_data=None, bytes_data=None):
        """
        Handles incoming WebSocket messages.
        Decodes the message, checks for throttling, and sends search results.

        :param text_data: JSON-encoded string containing the search query.
        :param bytes_data: Not used, as only text data is expected.
        """
        if await self.is_throttled():
            # Send an error message if the user is making requests too frequently.
            await self.send(text_data=json.dumps({'error': 'Too many requests'}))
            return

        # Parse the incoming JSON data.
        data = json.loads(text_data)
        query = data.get('query', '')

        # Fetch search suggestions based on the query.
        results = await self.get_search_suggestions(query)

        # Send the search results back to the client.
        await self.send(text_data=json.dumps({'results': results}))

    @database_sync_to_async
    def get_search_suggestions(self, query):
        """
        Fetches search suggestions for the given query.

        :param query: The search term provided by the client.
        :return: A list of up to 5 product names matching the query.
        """
        key = f"search_suggestions_{self.throttle_id}"
        past_results = cache.get(key)

        if past_results and query.startswith(cache.get(f"last_query_{self.throttle_id}", "")):
            # Filter cached results if the new query starts with the previous query
            filtered_results = [product for product in past_results if query.lower() in product[0].lower()]
        else:
            # Fetch results from the database and cache them
            products = Product.objects.all()
            filtered_products = search_products(products, query)[:20]
            filtered_results = list(filtered_products.values_list('name', 'description'))
            cache.set(key, filtered_results, timeout=1)  # Cache results for 1 second
            cache.set(f"last_query_{self.throttle_id}", query, timeout=1)  # Cache the last query

        # Return only the titles, limited to 5 results
        return [product[0] for product in filtered_results[:5]]

    async def is_throttled(self):
        """
        Checks if the client is making requests too frequently.

        :return: True if the client is throttled, False otherwise.
        """
        key = f"throttle_ws_{self.throttle_id}"
        now = time.time()
        cooldown = 0.5  # Minimum time (in seconds) between requests.

        # Retrieve the timestamp of the last request from the cache.
        last_request = cache.get(key)
        if last_request and now - last_request < cooldown:
            return True

        # Update the cache with the current timestamp.
        cache.set(key, now, timeout=5)
        return False
