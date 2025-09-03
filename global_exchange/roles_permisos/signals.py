from django.db.models.signals import post_migrate
from django.contrib.auth.models import Permission, Group
from django.contrib.auth import get_user_model
from django.dispatch import receiver

User = get_user_model()

# Traducciones estándar de permisos
TRADUCCIONES = {
    "Can add": "Puede agregar",
    "Can change": "Puede modificar",
    "Can delete": "Puede eliminar",
    "Can view": "Puede ver",
}

# Traducciones generales para palabras clave
TRADUCCIONES_NOMBRES = {
    "group": "rol",
    "permission": "permiso",
    "user": "usuario",
    "session": "sesión",
    "content type": "tipo de contenido"
}

SUPERADMIN_USERNAME = "superadmin"
SUPERADMIN_EMAIL = "admin@empresa.com"
SUPERADMIN_PASSWORD = "ContraseñaSegura123"
SUPERADMIN_CEDULA = "00000000" 

@receiver(post_migrate)
def configurar_inicial(sender, **kwargs):
    # Traducir permisos estándar solo si aún no se han traducido
    for codename, texto in TRADUCCIONES.items():
        permisos = Permission.objects.filter(name__startswith=codename)
        for permiso in permisos:
            parte_restante = permiso.name[len(codename):]
            nuevo_nombre = f"{texto}{parte_restante}"
            if permiso.name != nuevo_nombre:
                permiso.name = nuevo_nombre
                permiso.save()

    # Traducir palabras clave en permisos solo si es necesario
    permisos = Permission.objects.all()
    for permiso in permisos:
        nuevo_nombre = permiso.name
        for clave, traduccion in TRADUCCIONES_NOMBRES.items():
            if clave.lower() in nuevo_nombre.lower():
                nuevo_nombre = nuevo_nombre.replace(clave, traduccion)
        if nuevo_nombre != permiso.name:
            permiso.name = nuevo_nombre
            permiso.save()

    # Crear grupo ADMIN si no existe y asignar todos los permisos
    grupo_admin, creado_grupo = Group.objects.get_or_create(name="ADMIN")
    if creado_grupo or grupo_admin.permissions.count() != Permission.objects.count():
        grupo_admin.permissions.set(Permission.objects.all())
        grupo_admin.save()

    # Crear superadmin si no existe
    user, creado_user = User.objects.get_or_create(
        username=SUPERADMIN_USERNAME,
        defaults={
            "email": SUPERADMIN_EMAIL,
            "is_superuser": False,
            "is_staff": True,
            "is_active": True,
            "cedula": SUPERADMIN_CEDULA
        }
    )
    if creado_user:
        user.set_password(SUPERADMIN_PASSWORD)
        user.save()
        print("Superadmin creado correctamente.")

    # 6️⃣ Agregar superadmin al grupo ADMIN solo si no está
    if not user.groups.filter(name="ADMIN").exists():
        user.groups.add(grupo_admin)
        print("Superadmin agregado al grupo ADMIN.")

    print("Configuración completada.")
