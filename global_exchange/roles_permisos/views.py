from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from functools import wraps
from .models import Rol, Permiso
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
    """
    Vista que lista todos los roles y permisos disponibles.

    Contexto:
        - ``roles``: lista de roles ordenados por ID descendente.
        - ``permisos``: lista de permisos ordenados alfabéticamente.
        - ``form``: instancia vacía de ``RolForm`` para crear un nuevo rol.

    Plantilla:
        - ``roles/lista.html``
    """
    roles = Rol.objects.all().order_by('-id')
    permisos = Permiso.objects.all().order_by('nombre')
    form = RolForm()  # Formulario vacío para crear
    
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
            rol = form.save(commit=False)
            rol.save()
            # Guardar permisos
            permisos = request.POST.getlist('permisos')
            rol.permisos.set(permisos)
            return redirect("roles")
        else:
            roles = Rol.objects.all().order_by('-id')
            permisos_all = Permiso.objects.all().order_by('nombre')
            return render(request, "roles/lista.html", {
                "roles": roles, 
                "permisos": permisos_all,
                "form": form,
                "show_modal": True,
                "modal_type": "create",
            })
    return redirect("roles")


@superadmin_required
def rol_editar(request, pk):
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
    rol = get_object_or_404(Rol, pk=pk)

    if request.method == "POST":
        form = RolForm(request.POST, instance=rol)
        if form.is_valid():
            rol = form.save()
            permisos_ids = request.POST.getlist('permisos')
            rol.permisos.set(permisos_ids)
            return redirect("roles")
        else:
            # POST con errores: mostrar modal con errores
            roles = Rol.objects.filter(pk=pk)
            print(roles)
            permisos_all = Permiso.objects.all().order_by('nombre')
            return render(request, "roles/form.html", {
                "roles": roles,
                "form": form,
                "permisos": permisos_all,
                "modal_title": "Editar Rol",
                "form_action": request.path,
                "obj_id": rol.id,
            })
    else:
        # GET: abrir modal con form precargado
        form = RolForm(instance=rol)
        print(form)
        permisos_all = Permiso.objects.all().order_by('nombre')
        return render(request, "roles/lista.html", {
            "form": form,
            "permisos": permisos_all,
            "modal_title": "Editar Rol",
            "form_action": request.path,
            "obj_id": rol.id,
        })


@superadmin_required
def rol_eliminar(request, pk):
    """
    Vista que permite eliminar un rol existente.

    Parámetros:
        - ``pk``: ID del rol a eliminar.

    Flujo:
        - Si la petición es ``POST``, elimina el rol y redirige a ``roles``.
        - Si no es ``POST``, redirige directamente a ``roles``.
    """
    rol = get_object_or_404(Rol, pk=pk)
    if request.method == "POST":
        rol.delete()
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
    rol = get_object_or_404(Rol, pk=pk)
    print("rol detalle:", rol)
    permisos_ids = list(rol.permisos.values_list('id', flat=True))
    return JsonResponse({
        "nombre": rol.nombre,
        "descripcion": rol.descripcion,
        "permisos": permisos_ids
    })


