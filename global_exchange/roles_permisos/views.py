from django.shortcuts import render, get_object_or_404, redirect
from collections import namedtuple
from .models import Rol
from .forms import RolForm
from functools import wraps


# Solo superadmin
def superadmin_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated:
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            else:
                # Usuario normal no tiene acceso
                return redirect('home')
        return redirect('login')
    return _wrapped_view

@superadmin_required #con esto protejemos las rutas
def rol_lista(request):
    roles = Rol.objects.all().order_by('-id')
    return render(request, "roles.html", {"roles": roles})

@superadmin_required 
def rol_nuevo(request):
    if request.method == "POST":
        form = RolForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("roles")
    else:
        form = RolForm()
    return render(request, "rol_form.html", {"form": form})

@superadmin_required
def rol_editar(request, pk):
    rol = get_object_or_404(Rol, pk=pk)
    if request.method == "POST":
        form = RolForm(request.POST, instance=rol)
        if form.is_valid():
            form.save()
            return redirect("roles")
    else:
        form = RolForm(instance=rol)
    return render(request, "rol_form.html", {"form": form, "rol": rol})

@superadmin_required
def rol_eliminar(request, pk):
    rol = get_object_or_404(Rol, pk=pk)
    if request.method == "POST":
        rol.delete()
        return redirect("roles")
    return render(request, "rol_confirm_delete.html", {"rol": rol})