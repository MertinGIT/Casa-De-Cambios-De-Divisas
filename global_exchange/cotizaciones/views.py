from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from functools import wraps
from django.urls import reverse
from .models import TasaDeCambio, Moneda
from .forms import TasaDeCambioForm
from django.db.models import Q

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
def cotizacion_lista(request):
    tasas = TasaDeCambio.objects.all()
    form = TasaDeCambioForm()  # formulario vacío para crear nueva tasa
    q = request.GET.get("q", "").strip()
    campo = request.GET.get("campo", "").strip()
    
    # 🔍 Filtro de búsqueda
    if q:
        if campo == "moneda_destino":
            tasas = tasas.filter(moneda_destino__nombre__icontains=q)
        else:
            # Si no elige campo, buscar en ambos
            tasas = tasas.filter(
                Q(moneda_destino__nombre__icontains=q) |
                Q(moneda_origen__nombre__icontains=q)
            )
    
    return render(request, "cotizaciones/lista.html", {
        "tasas": tasas,
        "form": form,
        "modal_type": "create",  # 👈 siempre inicializado
        "obj_id": None,
        "q": q,
        "campo": campo 
    })


@superadmin_required
def cotizacion_nuevo(request):
    """
    Vista que permite crear una nueva cotización.
    """
    print("Entró en cotizacion_editar con pk =")
    if request.method == "POST":
        form = TasaDeCambioForm(request.POST)
        if form.is_valid():
            cotizacion = form.save(commit=False)
            cotizacion.estado = True
            cotizacion.save()
            # Si es AJAX devolvemos éxito en JSON
            print(cotizacion, flush=True)
            if request.headers.get("x-requested-with") == "XMLHttpRequest":
                return JsonResponse({
                    "success": True,
                    "tasa": {
                        "id": cotizacion.id,
                        "origen": cotizacion.moneda_origen.abreviacion,
                        "destino": cotizacion.moneda_destino.abreviacion,
                        "compra": str(cotizacion.monto_compra),
                        "venta": str(cotizacion.monto_venta),
                        "vigencia": cotizacion.vigencia.strftime("%d/%m/%Y %H:%M")
                    }
                })
            return redirect("cotizacion")
        else:
            print("123", flush=True)
            errors = {field: [str(e) for e in errs] for field, errs in form.errors.items()}
            if request.headers.get("x-requested-with") == "XMLHttpRequest":
                return JsonResponse({"success": False, "errors": errors})
            
            cotizaciones = TasaDeCambio.objects.all().order_by('-id')
            return render(request, "cotizaciones/lista.html", {
                "cotizaciones": cotizaciones,
                "form": form,
                "show_modal": True,
                "modal_type": "create",
            })
    return redirect("cotizacion")


@superadmin_required
def cotizacion_editar(request, pk):
    """
    Vista que permite editar una cotización existente.
    """
    print("Entró en cotizacion_editar con pk =", pk)
    cotizacion = get_object_or_404(TasaDeCambio, pk=pk)

    if request.method == "POST":
        form = TasaDeCambioForm(request.POST, instance=cotizacion)
        if form.is_valid():
            form.save()
            return redirect("cotizacion")
        else:
            # Si hay errores → reabrir modal con datos y errores
            errors = {field: [str(e) for e in errs] for field, errs in form.errors.items()}
            if request.headers.get("x-requested-with") == "XMLHttpRequest":
                return JsonResponse({"success": False, "errors": errors})
            cotizaciones = TasaDeCambio.objects.all().order_by('-id')
            return render(request, "cotizaciones/lista.html", {
                "cotizaciones": cotizaciones,
                "form": form,
                "show_modal": True,
                "obj_id": cotizacion.id, 
                "modal_type": "edit",
            })

    # Si entra por GET → mostrar lista y modal de edición abierto
    form = TasaDeCambioForm(instance=cotizacion)
    cotizaciones = TasaDeCambio.objects.all().order_by('-id')
    return render(request, "cotizaciones/lista.html", {
        "cotizaciones": cotizaciones,
        "form": form,
        "show_modal": True,
        "modal_type": "edit",
        "obj_id": cotizacion.id,
    })


@superadmin_required
@superadmin_required
def cotizacion_desactivar(request, pk):
    """
    Vista que permite eliminar una cotización existente.
    """
    cotizacion = get_object_or_404(TasaDeCambio, pk=pk)
    cotizacion.estado = not cotizacion.estado  # Alternar True/False
    cotizacion.save()
    return redirect("cotizacion")


@superadmin_required
def cotizacion_detalle(request, pk):
    """
    Vista que obtiene los datos de una cotización para edición mediante AJAX.
    """
    cotizacion = get_object_or_404(TasaDeCambio, pk=pk)
    return JsonResponse({
        "id": cotizacion.id,
        "moneda_origen": cotizacion.moneda_origen.id if cotizacion.moneda_origen else None,
        "moneda_destino": cotizacion.moneda_destino.id if cotizacion.moneda_destino else None,
        "monto_compra": float(cotizacion.monto_compra),
        "monto_venta": float(cotizacion.monto_venta),
        "vigencia": cotizacion.vigencia.strftime("%Y-%m-%d %H:%M:%S") if cotizacion.vigencia else None,
    })