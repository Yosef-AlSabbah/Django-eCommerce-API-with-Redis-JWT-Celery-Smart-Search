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
        response = renderer_context.get('response', None) if renderer_context else None

        # If data already has the expected keys, assume it's been wrapped
        if isinstance(data, dict) and "success" in data and "message" in data:
            return super().render(data, accepted_media_type, renderer_context)

        # Handle error responses (status codes >= 400)
        if response and response.status_code >= 400:
            if isinstance(data, dict):
                # Try to extract a meaningful message from common error keys
                if 'message' in data:
                    message = data.pop('message')
                elif 'error' in data:
                    message = data.pop('error')
                elif 'detail' in data:
                    message = data.pop('detail')
                else:
                    message = 'An error occurred'

                errors = data if data else None
            else:
                # Handle non-dict data (e.g., list of strings)
                message = 'An error occurred'
                errors = {'detail': data}

            return super().render(
                ApiResponse.error(message=message, status_code=response.status_code, errors=errors).data,
                accepted_media_type,
                renderer_context,
            )

        # Handle success responses (status codes < 400)
        return super().render(
            ApiResponse.success(data=data).data,
            accepted_media_type,
            renderer_context
        )
