from django import template

register = template.Library()

@register.filter
def has_active_group_perm(user, perm_codename):
    """
    Devuelve True si el usuario tiene el permiso y al menos uno de sus grupos activos lo otorga.
    Uso en template:
      {% if request.user|has_active_group_perm:'clientes.view_cliente' %}
    """
    if not user.is_authenticated:
        return False
    # Buscar grupos activos del usuario
    grupos_activos = user.groups.filter(profile__estado="Activo")
    # Para cada grupo activo, verificar si otorga el permiso
    for group in grupos_activos:
        if perm_codename in group.permissions.values_list('codename', flat=True) or \
           perm_codename in group.permissions.values_list('content_type__app_label', flat=True):
            if user.has_perm(f"{group.permissions.first().content_type.app_label}.{perm_codename}"):
                return True
    # Verificar si el usuario tiene el permiso directamente (no por grupo)
    if user.user_permissions.filter(codename=perm_codename.split('.')[-1]).exists():
        return True
    return False