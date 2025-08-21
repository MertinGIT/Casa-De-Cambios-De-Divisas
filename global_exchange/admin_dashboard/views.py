from django.shortcuts import render

# Create your views here.

def admin_dashboard(request):
    """
    Render the admin dashboard page.
    """
    return render(request, 'dashboard.html')