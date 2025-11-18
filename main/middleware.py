"""
Simple CORS middleware for Flutter web
"""
from django.http import HttpResponse

class CorsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Get the origin from the request (Flutter web will send this)
        origin = request.META.get('HTTP_ORIGIN', None)
        
        # For development, allow localhost origins
        # If no origin header, allow all (for non-browser clients)
        if origin:
            # Echo back the exact origin (required when using credentials)
            allow_origin = origin
            use_credentials = True
        else:
            # No origin header (e.g., from curl or non-browser client)
            allow_origin = '*'
            use_credentials = False
        
        # Handle preflight OPTIONS request
        if request.method == 'OPTIONS':
            response = HttpResponse()
            response['Access-Control-Allow-Origin'] = allow_origin
            response['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
            response['Access-Control-Allow-Headers'] = 'Content-Type, X-CSRFToken, Authorization, Accept'
            if use_credentials:
                response['Access-Control-Allow-Credentials'] = 'true'
            response['Access-Control-Max-Age'] = '86400'
            return response

        # Process the request
        response = self.get_response(request)

        # Add CORS headers to all responses
        # Use response.headers for Django 3.2+ or direct assignment for older versions
        if hasattr(response, 'headers'):
            response.headers['Access-Control-Allow-Origin'] = allow_origin
            if use_credentials:
                response.headers['Access-Control-Allow-Credentials'] = 'true'
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, X-CSRFToken, Authorization, Accept'
        else:
            response['Access-Control-Allow-Origin'] = allow_origin
            if use_credentials:
                response['Access-Control-Allow-Credentials'] = 'true'
            response['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
            response['Access-Control-Allow-Headers'] = 'Content-Type, X-CSRFToken, Authorization, Accept'

        return response

