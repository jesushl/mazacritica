from django.conf import settings
from django.http import HttpResponse

LOCAL_ORIGINS = {
    'http://127.0.0.1:5173',
    'http://localhost:5173',
}


class LocalDevCorsMiddleware:
    """Lets the Vite dev server read the API while DEBUG is on."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        origin = request.headers.get('Origin', '')
        allowed = bool(settings.DEBUG and origin in LOCAL_ORIGINS)
        if allowed and request.method == 'OPTIONS':
            response = HttpResponse(status=204)
        else:
            response = self.get_response(request)
        if allowed:
            response['Access-Control-Allow-Origin'] = origin
            response['Access-Control-Allow-Headers'] = 'authorization, content-type'
            response['Access-Control-Allow-Methods'] = 'GET, POST, PATCH, DELETE, OPTIONS'
            vary = response.get('Vary')
            response['Vary'] = f'{vary}, Origin' if vary else 'Origin'
        return response
