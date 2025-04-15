from rest_framework import renderers

from ecommerce_api.core.api_standard_response import ApiResponse


class ApiResponseRenderer(renderers.JSONRenderer):
    """
    Custom renderer that formats all API responses using a standardized structure.

    This renderer ensures that all responses (both success and error) conform to the
    `ApiResponse` format, providing consistency across the API.

    Features:
    - Automatically wraps successful responses in the `ApiResponse.success` format.
    - Automatically wraps error responses in the `ApiResponse.error` format.
    - Prevents double-wrapping of already formatted responses.
    """

    def render(self, data, accepted_media_type=None, renderer_context=None):
        """
        Render the response data into the standardized API response format.

        Args:
            data (Any): The data to be rendered in the response.
            accepted_media_type (str, optional): The accepted media type for the response.
            renderer_context (dict, optional): Additional context for rendering, including the response object.

        Returns:
            bytes: The rendered response in JSON format.
        """
        # Extract the response object from the renderer context
        response = renderer_context['response'] if renderer_context else None

        # Check if the response is already rendered (to avoid double-wrapping)
        if hasattr(response, 'is_rendered') and response.is_rendered:
            return super().render(data, accepted_media_type, renderer_context)

        # Handle error responses (status codes >= 400)
        if response and response.status_code >= 400:
            # Ensure `data` is a dictionary before attempting to pop keys
            if isinstance(data, dict):
                message = data.pop('message', 'An error occurred')  # Default error message
                errors = data if data else None  # Include remaining data as error details
            else:
                message = 'An error occurred'
                errors = None

            # Wrap the error response in the standardized format
            return super().render(
                ApiResponse.error(
                    message=message,
                    status_code=response.status_code,
                    errors=errors
                ).data,
                accepted_media_type,
                renderer_context
            )

        # Handle success responses (status codes < 400)
        return super().render(
            ApiResponse.success(data=data).data,  # Wrap the data in the success format
            accepted_media_type,
            renderer_context
        )
