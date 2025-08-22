from django.shortcuts import render, redirect
from functools import wraps

# Create your views here.

# Solo superadmin
def superadmin_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated:
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            else:
                # Usuario normal no tiene acceso
                return redirect('home')
        return redirect('login')
    return _wrapped_view


@superadmin_required 
def admin_dashboard(request):
    """
    Render the admin dashboard page.
    """
    return render(request, 'dashboard.html')