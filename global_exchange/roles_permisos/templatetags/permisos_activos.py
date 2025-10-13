from django import template

register = template.Library()

@register.filter
def has_active_group_perm(user, perm_codename):
    """
    Devuelve True si el usuario tiene el permiso directamente (no por grupo) o si al menos uno de sus grupos activos lo otorga.
    Uso en template:
      {% if request.user|has_active_group_perm:'clientes.view_cliente' %}
    """
    if not user.is_authenticated:
        return False
    # Extraer solo el codename (después del punto)
    codename = perm_codename.split('.')[-1]
    # Buscar grupos activos del usuario
    grupos_activos = user.groups.filter(profile__estado="Activo")
    for group in grupos_activos:
        if group.permissions.filter(codename=codename).exists():
            return True
    # Verificar si el usuario tiene el permiso directamente (no por grupo)
    if user.user_permissions.filter(codename=codename).exists():
        return True
    return False