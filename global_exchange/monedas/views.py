from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from functools import wraps
from .models import Moneda
from .forms import MonedaForm
from django.db.models import Q

# Decorador de superadmin
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


# LISTA
@superadmin_required
def moneda_lista(request):
    """
    Muestra la lista de monedas disponibles en el sistema, con opción de búsqueda y filtrado.

    La búsqueda se puede realizar por ``nombre`` o ``abreviacion``. Si no se especifica un campo,
    se buscará en ambos.

    :param request: Objeto HTTP con la información de la petición.
    :type request: HttpRequest
    :return: Render de la plantilla con la lista de monedas.
    :rtype: HttpResponse
    """
    monedas = Moneda.objects.all().order_by('-id')
    form = MonedaForm()  # formulario vacío para modal
    q = request.GET.get("q", "").strip()
    campo = request.GET.get("campo", "").strip()
    
    # 🔍 Filtro de búsqueda
    if q:
        if campo == "nombre":
            monedas = monedas.filter(nombre__icontains=q)
        elif campo == "abreviacion":
            monedas = monedas.filter(abreviacion__icontains=q)
        else:
            # Si no elige campo, buscar en ambos
            monedas = monedas.filter(
                Q(nombre__icontains=q) | Q(abreviacion__icontains=q)
            )

    return render(request, "monedas/lista.html", {
        "monedas": monedas,
        "form": form,
        "q": q,
        "campo": campo 
    })


# CREAR
@superadmin_required
def moneda_nueva(request):
    """
    Crea una nueva moneda en el sistema.

    - Si la petición es ``POST`` y el formulario es válido, guarda la moneda.
    - Si la petición es AJAX, devuelve un ``JsonResponse``.
    - Si hay errores en el formulario, se devuelven en la respuesta.

    :param request: Objeto HTTP con la información de la petición.
    :type request: HttpRequest
    :return: Redirección a la lista de monedas o ``JsonResponse``.
    :rtype: HttpResponse | JsonResponse
    """
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
    """
    Edita los datos de una moneda existente.

    - Si la petición es ``POST`` y el formulario es válido, guarda los cambios.
    - Si la petición es AJAX, devuelve un ``JsonResponse`` con el resultado.
    - Si hay errores, se devuelven en el contexto de la plantilla o en JSON.

    :param request: Objeto HTTP con la información de la petición.
    :type request: HttpRequest
    :param pk: ID de la moneda a editar.
    :type pk: int
    :return: Render de la plantilla, redirección o ``JsonResponse``.
    :rtype: HttpResponse | JsonResponse
    """
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


@superadmin_required
def moneda_desactivar(request, pk):
    """
    Activa o desactiva una moneda del sistema.

    Cambia el estado de la moneda al opuesto de su valor actual.

    :param request: Objeto HTTP con la información de la petición.
    :type request: HttpRequest
    :param pk: ID de la moneda a modificar.
    :type pk: int
    :return: Redirección a la lista de monedas.
    :rtype: HttpResponse
    """
    moneda = get_object_or_404(Moneda, pk=pk)
    # Cambiar el estado actual
    moneda.estado = not moneda.estado
    moneda.save()
    return redirect("monedas")


@superadmin_required
def moneda_detalle(request, pk):
    """
    Devuelve el detalle de una moneda en formato JSON.

    :param request: Objeto HTTP con la información de la petición.
    :type request: HttpRequest
    :param pk: ID de la moneda.
    :type pk: int
    :return: Información de la moneda en JSON.
    :rtype: JsonResponse
    """
    moneda = get_object_or_404(Moneda, pk=pk)
    return JsonResponse({
        "id": moneda.id,
        "nombre": moneda.nombre,
        "abreviacion": moneda.abreviacion,
    })

