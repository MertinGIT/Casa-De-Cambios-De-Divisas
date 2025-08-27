from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from functools import wraps
from django.contrib.auth.models import Group, Permission
from .forms import RolForm


# Solo superadmin
def superadmin_required(view_func):
    """
    Decorador que limita el acceso únicamente a usuarios superadministradores.

    - Si el usuario no está autenticado, se lo redirige a ``login``.
    - Si el usuario está autenticado pero no es superadmin, se lo redirige a ``home``.
    - Si el usuario es superadmin, se ejecuta la vista original.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated:
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            else:
                return redirect('home')
        return redirect('login')
    return _wrapped_view


@superadmin_required
def rol_lista(request):
    roles = Group.objects.all().order_by('-id')
    permisos = Permission.objects.all().order_by('name')
    form = RolForm()

    """
    Vista que lista todos los roles y permisos disponibles.

    Contexto:
        - ``roles``: lista de roles ordenados por ID descendente.
        - ``permisos``: lista de permisos ordenados alfabéticamente.
        - ``form``: instancia vacía de ``RolForm`` para crear un nuevo rol.

    Plantilla:
        - ``roles/lista.html``
    """

    return render(request, "roles/lista.html", {
        "roles": roles,
        "permisos": permisos,
        "form": form
    })


@superadmin_required
def rol_nuevo(request):
    """
    Vista que permite crear un nuevo rol.

    Flujo:
        - Si la petición es ``POST`` y el formulario es válido, guarda el rol y redirige a ``roles``.
        - Si hay errores de validación, recarga la lista de roles con el modal abierto mostrando los errores.
        - Si la petición no es ``POST``, redirige al listado de roles.

    Plantilla:
        - ``roles/lista.html`` (cuando hay errores)
    """
    if request.method == "POST":
        form = RolForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("roles")
    else:
        form = RolForm()
    permisos_all = Permission.objects.all().order_by('name')
    return render(request, "roles/lista.html", {
        "form": form,
        "permisos": permisos_all,
        "permisos_asignados": [],
        "show_modal": True,
        "modal_type": "create",
    })


@superadmin_required
def rol_editar(request, pk):
    group = get_object_or_404(Group, pk=pk)
    """
    Vista que permite editar un rol existente.

    Parámetros:
        - ``pk``: ID del rol a editar.

    Flujo:
        - Si la petición es ``POST`` y el formulario es válido, guarda los cambios y redirige a ``roles``.
        - Si hay errores de validación, recarga la lista de roles con el modal abierto mostrando los errores.
        - Si la petición no es ``POST``, redirige al listado de roles.

    Plantilla:
        - ``roles/lista.html`` (cuando hay errores)
    """
    if request.method == "POST":
        form = RolForm(request.POST, instance=group)
        if form.is_valid():
            form.save()
            return redirect("roles")
    else:
        form = RolForm(instance=group)
    permisos_all = Permission.objects.all().order_by('name')
    permisos_asignados = list(group.permissions.values_list('id', flat=True))
    return render(request, "roles/lista.html", {
        "form": form,
        "permisos": permisos_all,
        "permisos_asignados": permisos_asignados,
        "show_modal": True,
        "modal_type": "edit",
        "obj_id": group.id,
    })


@superadmin_required
def rol_eliminar(request, pk):
    group = get_object_or_404(Group, pk=pk)
    """
    Vista que permite eliminar un rol existente.

    Parámetros:
        - ``pk``: ID del rol a eliminar.

    Flujo:
        - Si la petición es ``POST``, elimina el rol y redirige a ``roles``.
        - Si no es ``POST``, redirige directamente a ``roles``.
    """
    if request.method == "POST":
        group.delete()
        return redirect("roles")
    return redirect("roles")


# Vista para obtener datos de un rol via AJAX (para llenar el modal de edición)
@superadmin_required
def rol_detalle(request, pk):
    """
    Vista que obtiene los datos de un rol para edición mediante AJAX.

    Parámetros:
        - ``pk``: ID del rol a consultar.

    Retorna:
        - JSON con:
            - ``id``: ID del rol.
            - ``nombre``: nombre del rol.
            - ``descripcion``: descripción del rol.
            - ``permisos``: lista de IDs de permisos asociados.
            - ``form_html``: HTML renderizado de los campos del formulario.

    Plantilla parcial:
        - ``roles/form_fields.html``
    """
    rol = get_object_or_404(Group, pk=pk)
    permisos_ids = list(map(str, rol.permissions.values_list('id', flat=True)))
    return JsonResponse({
        "name": rol.name,
        "permisos": permisos_ids,
        "modal_title": "Editar Rol"
    })
