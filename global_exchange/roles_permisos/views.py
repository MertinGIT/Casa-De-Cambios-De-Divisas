from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from functools import wraps
from django.contrib.auth.models import Group, Permission
from .forms import RolForm


# Solo superadmin
def superadmin_required(view_func):
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

    return render(request, "roles/lista.html", {
        "roles": roles,
        "permisos": permisos,
        "form": form
    })


@superadmin_required
def rol_nuevo(request):
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
        "show_modal": True,
        "modal_type": "create",
    })


@superadmin_required
def rol_editar(request, pk):
    group = get_object_or_404(Group, pk=pk)
    if request.method == "POST":
        form = RolForm(request.POST, instance=group)
        if form.is_valid():
            form.save()
            return redirect("roles")
    else:
        form = RolForm(instance=group)
    permisos_all = Permission.objects.all().order_by('name')
    return render(request, "roles/lista.html", {
        "form": form,
        "permisos": permisos_all,
        "show_modal": True,
        "modal_type": "edit",
        "obj_id": group.id,
    })


@superadmin_required
def rol_eliminar(request, pk):
    group = get_object_or_404(Group, pk=pk)
    if request.method == "POST":
        group.delete()
        return redirect("roles")
    return redirect("roles")


# Vista para obtener datos de un rol via AJAX (para llenar el modal de edición)
@superadmin_required
def rol_detalle(request, pk):
    rol = get_object_or_404(Group, pk=pk)
    permisos_ids = list(rol.permissions.values_list('id', flat=True))
    return JsonResponse({
        "name": rol.name,
        "permisos": permisos_ids
    })
