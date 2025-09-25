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

# from django.contrib import admin
from django.urls import path, include
from usuarios import views as usuarios_views, urls as usuarios_urls
from cliente_usuario import urls as cliente_usuario_urls
from admin_dashboard import views as admin_views
from django.conf.urls import handler404
from django.shortcuts import render
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from configuracion import views as configuracion_views
from operaciones import urls as operaciones_urls


urlpatterns = [

    path('clientes/', include('clientes.urls')), 
    # Clientes
    # path('admin/', admin.site.urls),
    path('', usuarios_views.pagina_aterrizaje, name='pagina_aterrizaje'),
    path('home/', usuarios_views.home, name='home'),
    path('signup/', usuarios_views.signup, name='signup'),
    path('logout/', usuarios_views.signout, name='signout'),
    path('login/', usuarios_views.signin, name='login'),
    path('editarperfil/', usuarios_views.editarPerfil, name='editarperfil'),
    path('activate/<uidb64>/<token>/', usuarios_views.activate, name='activate'),
    path('set_cliente_operativo/', usuarios_views.set_cliente_operativo, name='set_cliente_operativo'),
    path('operaciones/', include(operaciones_urls)),
    
    
    # Rutas solo para administradores
    path('admin/', admin_views.admin_dashboard, name='admin_dashboard'),
    path('admin/empleados/', usuarios_views.crud_empleados, name='empleados'),
    path('admin/forms/', TemplateView.as_view(template_name="forms.html"), name='forms'),
    path('admin/configuracion/segmentaciones/', include('cliente_segmentacion.urls')),
    path('admin/configuracion/', configuracion_views.configuracion_view, name='configuracion'),
    path('admin/configuracion/cotizaciones/', include('cotizaciones.urls'), name='cotizacion'),
    path('admin/configuracion/monedas/', include('monedas.urls'), name='moneda'),
    path('admin/configuracion/seguridad/usuarios/', include(usuarios_urls)),
    path('admin/configuracion/seguridad/roles/', include('roles_permisos.urls'), name='roles'),
    path("admin/configuracion/pagos/", include("metodos_pagos.urls"), name = 'metodos_pagos'),
    path('admin/cliente_usuario/', include(cliente_usuario_urls), name='cliente_usuario'),
    path('admin/clientes/', include('clientes.urls'), name = 'clientes'), 
    path('usuarios/', include('usuarios.urls')),
    path('limites/', include('limite_moneda.urls'))

]


def custom_404_view(request, exception):
    return render(request, "404.html", status=404)


handler404 = custom_404_view

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL,
                          document_root=settings.STATICFILES_DIRS[0])
