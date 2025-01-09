from django.contrib import messages


class ClearMessagesMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.endswith('/book-event/') and request.method == 'GET':
            storage = messages.get_messages(request)
            for _ in storage:
                pass  # Mark messages as used
            storage.used = True
            request.session.pop('messages', None)

        response = self.get_response(request)
        return response