"""global_exchange URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from usuarios import views
from clientes import views as clientes_views
from django.conf.urls import handler404
from django.shortcuts import render
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.pagina_aterrizaje, name='pagina_aterrizaje'),
    path('home/', views.home, name='home'),
    path('signup/', views.signup, name='signup'),
    path('logout/', views.signout, name='signout'),
    path('login/', views.signin, name='login'),
    path('editarperfil/', views.editarPerfil, name='editarperfil'),
    path('editarperfil-design/', views.editarperfilDesing, name='editarperfil'),
    path('admin/', admin.site.urls),
    path('activate/<uidb64>/<token>/', views.activate, name='activate'),
    path('empleados/', views.crud_empleados, name='empleados'),
    path('roles/', views.crud_roles, name='roles'),
    path('clientes/', include('clientes.urls')), 
    
]

def custom_404_view(request, exception):
    return render(request, "404.html", status=404)

handler404 = custom_404_view

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])

    
