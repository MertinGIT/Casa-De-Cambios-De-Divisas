from django.shortcuts import render, get_object_or_404, redirect
from collections import namedtuple
from .models import Rol
from .forms import RolForm

def rol_lista(request):
    roles = Rol.objects.all().order_by('-id')
    return render(request, "roles.html", {"roles": roles})

def rol_nuevo(request):
    if request.method == "POST":
        form = RolForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("rol_lista")
    else:
        form = RolForm()
    return render(request, "rol_form.html", {"form": form})

def rol_editar(request, pk):
    rol = get_object_or_404(Rol, pk=pk)
    if request.method == "POST":
        form = RolForm(request.POST, instance=rol)
        if form.is_valid():
            form.save()
            return redirect("rol_lista")
    else:
        form = RolForm(instance=rol)
    return render(request, "rol_form.html", {"form": form, "rol": rol})

def rol_eliminar(request, pk):
    rol = get_object_or_404(Rol, pk=pk)
    if request.method == "POST":
        rol.delete()
        return redirect("rol_lista")
    return render(request, "rol_confirm_delete.html", {"rol": rol})