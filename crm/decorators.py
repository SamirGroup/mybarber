from django.contrib.auth.decorators import user_passes_test
from functools import wraps

def admin_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.user.is_superuser or request.user.is_staff:
            return view_func(request, *args, **kwargs)
        from django.shortcuts import redirect
        from django.contrib import messages
        messages.error(request, "You don't have permission to access this page.")
        return redirect('dashboard')
    return wrapper

def barber_or_admin_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated and (request.user.is_superuser or request.user.is_staff or hasattr(request.user, 'barber')):
            return view_func(request, *args, **kwargs)
        from django.shortcuts import redirect
        from django.contrib import messages
        messages.error(request, "You don't have permission to access this page.")
        return redirect('dashboard')
    return wrapper