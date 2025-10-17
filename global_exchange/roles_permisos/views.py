from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from roles_permisos.middleware import require_permission
from django.contrib.auth.models import Group, Permission
from django.core.paginator import Paginator
from .forms import RolForm

@require_permission('view_customuser')
def rol_lista(request):
    """
    Vista que lista todos los roles y permisos disponibles.

    Parameters
    ----------
    request : HttpRequest
        Objeto de la petición HTTP.

    Returns
    -------
    HttpResponse
        Renderizado de la plantilla ``roles/lista.html``.

    Contexto
    --------
    - ``roles``: lista de roles ordenados por ID descendente.
    - ``permisos``: lista de permisos ordenados alfabéticamente.
    - ``form``: instancia vacía de :class:`.forms.RolForm` para crear un nuevo rol.

    Template
    --------
    - ``roles/lista.html``
    """
    roles = Group.objects.all().order_by("-id")

    # --- Filtro de búsqueda ---
    q = request.GET.get("q", "").strip()
    campo = request.GET.get("campo", "").strip()

    if q:
        if campo == "nombre":
            roles = roles.filter(name__icontains=q)

    # --- Paginación ---
    paginator = Paginator(roles, 10)  # 10 registros por página
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    permisos = Permission.objects.all().order_by("name")
    form = RolForm()
    return render(request, "roles/lista.html", {
        "roles": page_obj.object_list,
        "permisos": permisos,
        "form": form,
        "page_obj": page_obj,
        "q": q,
        "campo": campo,
    })


def rol_nuevo(request):
    """
    Vista que permite crear un nuevo rol.

    Parameters
    ----------
    request : HttpRequest
        Objeto de la petición HTTP.

    Returns
    -------
    HttpResponse
        Redirige al listado de roles o renderiza la plantilla
        ``roles/lista.html`` si hay errores.

    Flujo
    -----
    - Si la petición es ``POST`` y el formulario es válido, guarda el rol y redirige a ``roles``.
    - Si hay errores de validación, recarga la lista de roles con el modal abierto mostrando los errores.
    - Si la petición no es ``POST``, muestra el formulario vacío.

    Template
    --------
    - ``roles/lista.html``
    """
    if request.method == "POST":
        form = RolForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("roles")
    else:
        form = RolForm()
    permisos_all = Permission.objects.all().order_by("name")

    # --- Aseguramos paginación en modal ---
    roles = Group.objects.all().order_by("-id")

    # Mantener filtro de búsqueda si viene en la querystring
    q = request.GET.get("q", "").strip()
    campo = request.GET.get("campo", "").strip()
    if q and campo == "nombre":
        roles = roles.filter(name__icontains=q)

    paginator = Paginator(roles, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, "roles/lista.html", {
        "form": form,
        "permisos": permisos_all,
        "permisos_asignados": [],
        "show_modal": True,
        "modal_type": "create",
        "roles": page_obj.object_list,
        "page_obj": page_obj,
        "q": q,
        "campo": campo,
    })


def rol_editar(request, pk):
    """
    Vista que permite editar un rol existente.

    Parameters
    ----------
    request : HttpRequest
        Objeto de la petición HTTP.
    pk : int
        ID del rol a editar.

    Returns
    -------
    HttpResponse
        Redirige al listado de roles o renderiza la plantilla
        ``roles/lista.html`` con errores.

    Template
    --------
    - ``roles/lista.html`` (cuando hay errores o modal activo).
    """
    group = get_object_or_404(Group, pk=pk)
    if request.method == "POST":
        form = RolForm(request.POST, instance=group)
        if form.is_valid():
            form.save()
            return redirect("roles")
    else:
        form = RolForm(instance=group)
    permisos_all = Permission.objects.all().order_by("name")
    permisos_asignados = list(group.permissions.values_list("id", flat=True))

    # --- Aseguramos paginación en modal ---
    roles = Group.objects.all().order_by("-id")

    # Mantener filtro de búsqueda si viene en la querystring
    q = request.GET.get("q", "").strip()
    campo = request.GET.get("campo", "").strip()
    if q and campo == "nombre":
        roles = roles.filter(name__icontains=q)

    paginator = Paginator(roles, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, "roles/lista.html", {
        "form": form,
        "permisos": permisos_all,
        "permisos_asignados": permisos_asignados,
        "show_modal": True,
        "modal_type": "edit",
        "obj_id": group.id,
        "roles": page_obj.object_list,
        "page_obj": page_obj,
        "q": q,
        "campo": campo,
    })


def rol_eliminar(request, pk):
    """
    Vista que permite eliminar (desactivar) un rol existente.

    Parameters
    ----------
    request : HttpRequest
        Objeto de la petición HTTP.
    pk : int
        ID del rol a eliminar.

    Returns
    -------
    HttpResponse
        Redirige al listado de roles.

    Flujo
    -----
    - Si la petición es ``POST`` y el rol tiene perfil, cambia su estado a ``Activo``.
    - Si el rol no tiene perfil, crea uno y lo marca como ``Activo``.
    """
    group = get_object_or_404(Group, pk=pk)
    if hasattr(group, "profile"):
        if request.method == "POST":
            group.profile.estado = "Activo"
            group.profile.save()
            return redirect("roles")
    else:
        from roles_permisos.models import GroupProfile
        GroupProfile.objects.create(group=group, estado="Activo")
        return redirect("roles")
    return redirect("roles")


def rol_activar(request, pk):
    """
    Vista que activa un rol existente.

    Parameters
    ----------
    request : HttpRequest
        Objeto de la petición HTTP.
    pk : int
        ID del rol a activar.

    Returns
    -------
    HttpResponse
        Redirige al listado de roles.
    """
    group = get_object_or_404(Group, pk=pk)
    if hasattr(group, "profile"):
        group.profile.estado = "Activo"
        group.profile.save()
    else:
        from roles_permisos.models import GroupProfile
        GroupProfile.objects.create(group=group, estado="Activo")
    return redirect("roles")


def rol_desactivar(request, pk):
    """
    Vista que desactiva un rol existente.

    Parameters
    ----------
    request : HttpRequest
        Objeto de la petición HTTP.
    pk : int
        ID del rol a desactivar.

    Returns
    -------
    HttpResponse
        Redirige al listado de roles.
    """
    group = get_object_or_404(Group, pk=pk)
    if hasattr(group, "profile"):
        group.profile.estado = "Inactivo"
        group.profile.save()
    else:
        from roles_permisos.models import GroupProfile
        GroupProfile.objects.create(group=group, estado="Inactivo")
    return redirect("roles")


def rol_detalle(request, pk):
    """
    Vista que obtiene los datos de un rol para edición mediante AJAX.

    Parameters
    ----------
    request : HttpRequest
        Objeto de la petición HTTP.
    pk : int
        ID del rol a consultar.

    Returns
    -------
    JsonResponse
        Un JSON con los datos del rol:
        - ``name``: nombre del rol.
        - ``permisos``: lista de IDs de permisos asociados.
        - ``modal_title``: título del modal de edición.

    Template parcial
    ----------------
    - ``roles/form_fields.html``
    """
    rol = get_object_or_404(Group, pk=pk)
    permisos_ids = list(map(str, rol.permissions.values_list("id", flat=True)))
    return JsonResponse({
        "name": rol.name,
        "permisos": permisos_ids,
        "modal_title": "Editar Rol",
    })
