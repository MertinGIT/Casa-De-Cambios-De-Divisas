"""
Middleware de control por URL y roles
Crea un archivo middleware.py dentro de tu app y pon esto
"""

from django.shortcuts import redirect, render
from django.urls import reverse
from django.contrib.auth.models import Group
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib import messages
import re


class RoleBasedMiddleware:
    """
    Middleware que verifica acceso a ciertas rutas según roles de usuario.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        # Reglas de acceso por ruta
        self.access_rules = {
            # Solo ADMIN y Analista pueden acceder a estas rutas
             r"^/admin/.*$": ['ADMIN', 'Analista'], 
             r"^/clientes/.*$": ['ADMIN','Analista'], 
            
            # Usuarios comunes pueden acceder solo a ciertas rutas
            '/home/': ['Usuario', 'Usuario Asociado', 'Usuario'],
            '/editarperfil/': ['Usuario Asociado', 'Usuario'],
            '/operaciones/': ['Usuario Asociado'],
            '/historial/': ['Usuario Asociado'],
            '/medios_acreditacion/': ['Usuario Asociado'],
            '/medios_acreditacion/': ['Usuario Asociado'],
            '/configuracion/mfa_configuration/': ['Usuario Asociado'],
        }

    def __call__(self, request):
        path = request.path

        # Si no es una ruta protegida, continuar
        if not self._is_protected_route(path):
            response = self.get_response(request)
            return response

        # Si el usuario no está autenticado
        if not request.user.is_authenticated:
            return redirect('login')

        # Verificar acceso según grupos
        if self._user_has_access(request.user, path):
            response = self.get_response(request)
            return response
        else:
            # Usuario no tiene permisos
            return render(request, "403.html", status=403)


    def _is_protected_route(self, path):
        """Verifica si la ruta está protegida usando regex"""
        for route in self.access_rules:
            if re.match(route, path):
                return True
        return False


    def _user_has_access(self, user, path):
        """Verifica si el usuario tiene acceso a cierta ruta según roles activos"""
        for route, roles in self.access_rules.items():
            if re.match(route, path):  # <-- regex match
                # Filtrar solo los roles activos del usuario
                user_roles_activos = user.groups.filter(
                    name__in=roles,
                    profile__estado="Activo"
                )
                return user_roles_activos.exists()
        return True 


# Decorador alternativo para vistas específicas
def require_role(allowed_roles):
    """
    Decorador para requerir ciertos roles en vistas específicas
    Uso: @require_role(['Administrador', 'Superadmin'])
    """
    def decorator(view_func):
        @login_required
        def wrapped_view(request, *args, **kwargs):

            # Verificar si el usuario tiene alguno de los roles requeridos
            if request.user.groups.filter(name__in=allowed_roles).exists():
                return view_func(request, *args, **kwargs)
            else:
                return render(request, "403.html", status=403)
        return wrapped_view
    return decorator


# Decorador para permisos específicos
def require_permission(permission_codename):
    """
    Decorador para requerir un permiso específico
    Uso: @require_permission('can_view_clients')
    """
    def decorator(view_func):
        @login_required
        def wrapped_view(request, *args, **kwargs):
            if request.user.has_perm(permission_codename):
                return view_func(request, *args, **kwargs)
            else:
                return render(request, "403.html", status=403)
        return wrapped_view
    return decorator