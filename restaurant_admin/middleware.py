# restaurant_admin/middleware.py
from django.http import JsonResponse

class StoreStatusMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            response = self.get_response(request)
            return response
        except Exception as e:
            if request.path == '/order/check-store-status/':
                return JsonResponse({
                    'status': 'error',
                    'message': 'An error occurred while checking store status'
                }, status=500)
            raise