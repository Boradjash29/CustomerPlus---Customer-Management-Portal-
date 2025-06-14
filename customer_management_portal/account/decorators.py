from django.http import HttpResponse
from django.shortcuts import redirect

# Decorator to restrict access to unauthenticated users only
def unauthenticated_user(view_func):
    def wrapper_func(request, *args, **kwargs):
        if request.user.is_authenticated:
            # Get all group names the user belongs to
            group_names = [group.name for group in request.user.groups.all()]
            
            if 'admin' in group_names:
                return redirect('home')  # Admin dashboard
            elif 'customer' in group_names:
                return redirect('user-page')  # Customer dashboard
            else:
                return redirect('home')  # Fallback redirect if group unknown
        return view_func(request, *args, **kwargs)
    return wrapper_func

# Decorator to allow access only to users with specified group(s)
def allowed_users(allowed_roles=[]):
    def decorator(view_func):
        def wrapper_func(request, *args, **kwargs):
            if request.user.groups.exists():
                user_groups = [group.name for group in request.user.groups.all()]
                if any(group in allowed_roles for group in user_groups):
                    return view_func(request, *args, **kwargs)
            return HttpResponse("You are not authorized to view this page.")
        return wrapper_func
    return decorator

# Decorator to allow access only to admin users
def admin_only(view_func):
    def wrapper_func(request, *args, **kwargs):
        if request.user.groups.exists():
            user_groups = [group.name for group in request.user.groups.all()]
            if 'admin' in user_groups:
                return view_func(request, *args, **kwargs)
            elif 'customer' in user_groups:
                return redirect('user-page')  # Redirect customers
        return HttpResponse(" You are not authorized to view this page.")
    return wrapper_func
