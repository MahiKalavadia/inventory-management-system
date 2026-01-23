from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required


def role_required(role_name):
    def decorator(view_func):
        @login_required
        def wrapper(request, *args, **kwargs):
            # Allow superuser always
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            # Check group role
            if request.user.groups.filter(name=role_name).exists():
                return view_func(request, *args, **kwargs)
            # Block unauthorized users
            return redirect("login")

        return wrapper
    return decorator
