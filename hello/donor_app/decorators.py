from django.http import HttpResponseForbidden
from functools import wraps

def role_required(roles=[]):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if request.user.user_type not in roles:
                return HttpResponseForbidden("You don't have permission to access this page")
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator