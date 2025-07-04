from django.contrib.auth import logout
from django.shortcuts import redirect
from django.utils import timezone
from django.conf import settings
import datetime

class AutoLogoutMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        if request.user.is_authenticated:
            last_activity = request.session.get('last_activity')
            if last_activity:
                last_activity = datetime.datetime.fromisoformat(last_activity)
                if (timezone.now() - last_activity).seconds > settings.SESSION_COOKIE_AGE:
                    logout(request)
                    return redirect('login?timeout=1')
            request.session['last_activity'] = timezone.now().isoformat()
        response = self.get_response(request)
        return response