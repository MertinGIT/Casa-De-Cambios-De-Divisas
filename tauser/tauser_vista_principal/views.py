from django.shortcuts import render

def login_view(request):
    """Renderiza el formulario de login"""
    return render(request, "login.html")
