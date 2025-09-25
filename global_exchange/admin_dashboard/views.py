from django.shortcuts import render, redirect
from functools import wraps

# Create your views here.

def admin_dashboard(request):
    """
    Renderiza la página del panel de administración.
    """
    return render(request, 'dashboard.html')