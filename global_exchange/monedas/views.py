from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from functools import wraps
from .models import Moneda
from .forms import MonedaForm

# Decorador de superadmin
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


# LISTA
@superadmin_required
def moneda_lista(request):
    monedas = Moneda.objects.all().order_by('-id')
    form = MonedaForm()  # formulario vacío para modal

    return render(request, "monedas/lista.html", {
        "monedas": monedas,
        "form": form,
    })


# CREAR
@superadmin_required
def moneda_nueva(request):
    if request.method == "POST":
        form = MonedaForm(request.POST)
        if form.is_valid():
            form.save()
            if request.headers.get("x-requested-with") == "XMLHttpRequest":
                return JsonResponse({"success": True})
            return redirect("monedas")
        else:
            errors = {field: [str(e) for e in errs] for field, errs in form.errors.items()}
            if request.headers.get("x-requested-with") == "XMLHttpRequest":
                return JsonResponse({"success": False, "errors": errors})
            monedas = Moneda.objects.all().order_by('-id')
            return render(request, "monedas/lista.html", {
                "monedas": monedas,
                "form": form,
                "show_modal": True,
                "modal_type": "create",
            })
    return redirect("monedas")



# EDITAR
@superadmin_required
def moneda_editar(request, pk):
    moneda = get_object_or_404(Moneda, pk=pk)
    if request.method == "POST":
        form = MonedaForm(request.POST, instance=moneda)
        if form.is_valid():
            form.save()
            # ✅ IMPORTANTE: devolver JsonResponse si es AJAX
            if request.headers.get("x-requested-with") == "XMLHttpRequest":
                return JsonResponse({"success": True})
            return redirect("monedas")
        else:
            errors = {field: [str(e) for e in errs] for field, errs in form.errors.items()}
            if request.headers.get("x-requested-with") == "XMLHttpRequest":
                return JsonResponse({"success": False, "errors": errors})
            monedas = Moneda.objects.all().order_by('-id')
            return render(request, "monedas/lista.html", {
                "monedas": monedas,
                "form": form,
                "show_modal": True,
                "modal_type": "edit",
                "obj_id": moneda.id,
            })
    else:
        form = MonedaForm(instance=moneda)
        monedas = Moneda.objects.all().order_by('-id')
        return render(request, "monedas/lista.html", {
            "monedas": monedas,
            "form": form,
            "show_modal": True,
            "modal_type": "edit",
            "obj_id": moneda.id,
        })


# ELIMINAR
@superadmin_required
def moneda_eliminar(request, pk):
    moneda = get_object_or_404(Moneda, pk=pk)
    if request.method == "POST":
        moneda.delete()
        return redirect("monedas")
    return redirect("monedas")


@superadmin_required
def moneda_detalle(request, pk):
    moneda = get_object_or_404(Moneda, pk=pk)
    return JsonResponse({
        "id": moneda.id,
        "nombre": moneda.nombre,
        "abreviacion": moneda.abreviacion,
    })

