from rest_framework.pagination import PageNumberPagination

from ecommerce_api.core.api_standard_response import ApiResponse


# Custom pagination class extending DRF's PageNumberPagination
class CustomPageNumberPagination(PageNumberPagination):
    # Default number of items per page
    page_size = 10
    # Query parameter to allow clients to set the page size
    page_size_query_param = 'page_size'
    # Maximum allowed page size
    max_page_size = 100
    # Query parameter for the page number
    page_query_param = 'page'

    def get_paginated_response(self, data):
        """
        Generate a paginated response using the standardized API response format.

        Args:
            data: The paginated data to include in the response.

        Returns:
            Response: A DRF Response object with pagination metadata and data.
        """
        return ApiResponse.success(
            data=data,  # The paginated data
            meta={
                'pagination': {
                    'next': self.get_next_link(),  # URL for the next page, if available
                    'previous': self.get_previous_link(),  # URL for the previous page, if available
                    'count': self.page.paginator.count,  # Total number of items
                    'current_page': self.page.number,  # Current page number
                    'total_pages': self.page.paginator.num_pages,  # Total number of pages
                    'page_size': self.get_page_size(self.request)  # Number of items per page
                }
            }
        )
