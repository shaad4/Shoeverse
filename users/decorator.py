from django.shortcuts import redirect
from functools import wraps

def user_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("login")  # redirect to normal user login

        
        if hasattr(request.user, "role") and request.user.role != "user":
            return redirect("login")

        return view_func(request, *args, **kwargs)
    return wrapper
