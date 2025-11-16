from django.shortcuts import redirect
from functools import wraps

def admin_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("admin_login")
        if request.user.role != "admin":
            return redirect("admin_login")
        return view_func(request, *args, **kwargs)
    return wrapper