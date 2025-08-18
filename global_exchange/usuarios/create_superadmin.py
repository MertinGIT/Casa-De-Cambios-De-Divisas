import os
import sys
import django

# Agregamos la raíz del proyecto al path de Python
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configuramos Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "global_exchange.settings")
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

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
