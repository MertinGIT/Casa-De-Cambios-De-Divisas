from django.db.models.signals import post_migrate
from django.contrib.auth.models import Permission, Group
from django.contrib.auth import get_user_model
from django.dispatch import receiver
from roles_permisos.models import GroupProfile

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

    # Crear grupo USUARIO si no existe y asignar permisos con codename "view_*"
    grupo_usuario, creado_usuario = Group.objects.get_or_create(name="Usuario")
    if creado_usuario:
        permisos_view = Permission.objects.filter(codename__startswith="view_")
        grupo_usuario.permissions.set(permisos_view)
        grupo_usuario.save()
    else:
        # Verificar si necesita actualizar permisos
        permisos_view = Permission.objects.filter(codename__startswith="view_")
        if grupo_usuario.permissions.count() != permisos_view.count():
            grupo_usuario.permissions.set(permisos_view)
            grupo_usuario.save()

    # Crear grupo USUARIO ASOCIADO si no existe
    grupo_usuario_asociado, creado_asociado = Group.objects.get_or_create(name="Usuario Asociado")
    
    # Obtener permisos para Usuario Asociado:
    permisos_view = Permission.objects.filter(codename__startswith="view_")
    permisos_usuario_especificos = Permission.objects.filter(
        codename__in=["add_customuser", "view_customuser", "change_customuser", "add_metodopago"
                      , "view_medioacreditacion", "add_medioacreditacion", "add_transaccion", "view_transaccion"]
    )
    
    permisos_usuario_asociado = permisos_view.union(permisos_usuario_especificos)
    
    if creado_asociado:
        grupo_usuario_asociado.permissions.set(permisos_usuario_asociado)
        grupo_usuario_asociado.save()
    else:
        permisos_actuales = set(grupo_usuario_asociado.permissions.values_list('id', flat=True))
        permisos_esperados = set(permisos_usuario_asociado.values_list('id', flat=True))
        
        if permisos_actuales != permisos_esperados:
            grupo_usuario_asociado.permissions.set(permisos_usuario_asociado)
            grupo_usuario_asociado.save()
    
    # Crear GroupProfiles si no existen
    GroupProfile.objects.get_or_create(
        group=grupo_admin,
        defaults={'estado': 'Activo'}
    )
    GroupProfile.objects.get_or_create(
        group=grupo_usuario,
        defaults={'estado': 'Activo'}
    )
    GroupProfile.objects.get_or_create(
        group=grupo_usuario_asociado,
        defaults={'estado': 'Activo'}
    )

    # Crear superadmin si no existe
    user, creado_user = User.objects.get_or_create(
        username=SUPERADMIN_USERNAME,
        defaults={
            "email": SUPERADMIN_EMAIL,
            "is_superuser": False,
            "is_staff": False,
            "is_active": True,
            "cedula": SUPERADMIN_CEDULA
        }
    )
    if creado_user:
        user.set_password(SUPERADMIN_PASSWORD)
        user.save()

    # Agregar superadmin al grupo ADMIN solo si no está
    if not user.groups.filter(name="ADMIN").exists():
        user.groups.add(grupo_admin)



    # Crear grupo ANALISTA si no existe
    grupo_analista, creado_analista = Group.objects.get_or_create(name="Analista")
    # Permisos base: igual que Usuario Asociado
    permisos_analista = set(grupo_usuario_asociado.permissions.all())
    # Permisos extra: Cliente, Medio de acreditación, Medio de pago, Tipo Entidad Financiera
    modelos_permisos_extra = [
        ("clientes", "cliente"),
        ("medio_acreditacion", "medioacreditacion"),
        ("metodos_pagos", "metodopago"),
        ("medio_acreditacion", "tipoentidadfinanciera"),
        ("cliente_usuario", "usuario_cliente")
    ]
    acciones = ["add_", "view_", "change_"]
    for app_label, model in modelos_permisos_extra:
        for accion in acciones:
            codename = f"{accion}{model}"
            try:
                permiso = Permission.objects.get(codename=codename, content_type__app_label=app_label)
                permisos_analista.add(permiso)
            except Permission.DoesNotExist:
                pass
    # Agregar permisos personalizados de compra/venta de divisa
    grupo_analista.permissions.set(permisos_analista)
    grupo_analista.save()
    GroupProfile.objects.get_or_create(
        group=grupo_analista,
        defaults={'estado': 'Activo'}
    )

print("Configuración completada.")
