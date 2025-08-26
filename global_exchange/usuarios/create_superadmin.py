import os
import sys
import django
"""
Script para crear un superusuario manual en Django.

Este módulo permite crear un superadministrador en la base de datos
de manera programática. Útil para inicializar el proyecto o agregar
un superadmin cuando no se desea usar `createsuperuser`.

Funciones:
    crear_superadmin_manual(): Crea un superusuario con credenciales
        predeterminadas si no existe aún.
"""
# Agregamos la raíz del proyecto al path de Python
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configuramos Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "global_exchange.settings")
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

"""
    Crea un superadministrador manualmente.

    Crea un usuario con permisos de superusuario, staff y activo,
    usando credenciales predeterminadas. Solo se crea si no existe
    un usuario con el mismo username.

    Campos por defecto:
        - username (str): "superadmin"
        - email (str): "admin@empresa.com"
        - password (str): "ContraseñaSegura123"
        -cedula (str): "00000000"

    Comportamiento:
        - Verifica si el username ya existe en la base de datos.
        - Si no existe, crea el usuario con los atributos mencionados
          y guarda la contraseña de forma segura.
        - Imprime mensajes indicando si se creó el usuario o si ya
          existía.
    """
def crear_superadmin_manual():
    username = "superadmin"
    email = "admin@empresa.com"
    password = "ContraseñaSegura123"
    cedula = "00000000"

    if not User.objects.filter(username=username).exists():
        user = User(
            username=username,
            email=email,
            cedula=cedula,
            is_superuser=True,
            is_staff=True,
            is_active=True
        )
        user.set_password(password)
        user.save()
        print("Superadmin creado correctamente.")
    else:
        print("El superadmin ya existe.")

if __name__ == "__main__":
    crear_superadmin_manual()
