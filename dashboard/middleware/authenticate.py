from django.shortcuts import redirect
from django.urls import reverse

class AuthMiddleware:
    def __init__(self, get_response):
        self.getresponse = get_response

    def __call__(self, request):

        if request.path.startswith('/dashboard/'):
            exempt_urls = [
                reverse('loginpage'),
                reverse('logoutuser'),
                '/admin/',
                '/static/',
            ]

            if not any(request.path.endswith(url) for url in exempt_urls):
                if not request.user.is_authenticated:
                    return redirect('loginpage')

        response = self.getresponse(request)
        return response
