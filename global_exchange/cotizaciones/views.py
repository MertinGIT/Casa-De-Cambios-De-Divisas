from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from functools import wraps
from django.urls import reverse
from .models import TasaDeCambio, Moneda
from .forms import TasaDeCambioForm
from django.db.models import Q
from datetime import datetime

def cotizacion_lista(request):
    """
    Vista que lista todas las tasas de cambio.

    - Solo accesible por superadministradores.
    - Permite filtrar resultados por nombre de moneda de origen o destino.
    - Devuelve el template ``cotizaciones/lista.html`` con:
        - tasas: queryset filtrado y ordenado por vigencia.
        - form: formulario vacío de TasaDeCambioForm (para crear nuevas tasas).
        - q: cadena de búsqueda.
        - campo: campo seleccionado para filtrar.
    """
    tasas = TasaDeCambio.objects.filter(
        moneda_origen__estado=True,
        moneda_destino__estado=True
    ).order_by('-vigencia')
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

    # 🔹 Mantener orden por vigencia después del filtro
    tasas = tasas.order_by('-vigencia')

    return render(request, "cotizaciones/lista.html", {
        "tasas": tasas,
        "form": form,
        "modal_type": "create",  
        "obj_id": None,
        "q": q,
        "campo": campo,
    })



def cotizacion_nuevo(request):
    """
    Vista que permite crear una nueva cotización de monedas.

    - Método: POST
    - Si el formulario es válido:
        - Se guarda la nueva tasa con estado=True.
        - Si la petición es AJAX → devuelve JSON con los datos de la tasa creada.
        - Si no es AJAX → redirige a ``cotizacion``.
    - Si el formulario no es válido:
        - Para AJAX → devuelve JSON con errores de validación.
        - Para no-AJAX → renderiza la lista mostrando el modal con errores.
    - Si no es POST → redirige a ``cotizacion``.
    """
    print("Entró en cotizacion_editar con pk =")
    if request.method == "POST":
        form = TasaDeCambioForm(request.POST)
        if form.is_valid():
            cotizacion = form.save(commit=False)
            cotizacion.estado = True
            # Los valores de comisión ya están en el form, no sobrescribir
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
                "tasas": cotizaciones,
                "form": form,
                "show_modal": True,
                "modal_type": "create",
            })
    return redirect("cotizacion")

def cotizacion_editar(request, pk):
    """
    Edita una cotización existente de TasaDeCambio.

    Esta vista maneja tanto solicitudes GET como POST. En el caso de POST,
    valida y guarda los cambios del formulario, manteniendo el estado original
    de la cotización. Responde con JSON si la solicitud es AJAX o redirige
    a la lista de cotizaciones en solicitudes normales. En caso de errores,
    vuelve a mostrar el modal con los mensajes de validación.

    """
    
    cotizacion = get_object_or_404(TasaDeCambio, pk=pk)

    if request.method == "POST":
        form = TasaDeCambioForm(request.POST, instance=cotizacion)
        if form.is_valid():
            cotizacion = form.save(commit=False)
            cotizacion.estado = TasaDeCambio.objects.get(pk=cotizacion.pk).estado
            cotizacion.save()
            
            if request.headers.get("x-requested-with") == "XMLHttpRequest":
                return JsonResponse({
                    "success": True,
                    "tasa": {
                        "id": cotizacion.id,
                        "moneda_origen": cotizacion.moneda_origen.nombre,
                        "moneda_destino": cotizacion.moneda_destino.nombre,
                        "compra": str(cotizacion.monto_compra),
                        "venta": str(cotizacion.monto_venta),
                        "estado": cotizacion.estado,
                    }
                })
            else:
                return redirect("cotizacion")
        else:
            # reabrir modal con errores
            errors = {field: [str(e) for e in errs] for field, errs in form.errors.items()}
            if request.headers.get("x-requested-with") == "XMLHttpRequest":
                return JsonResponse({"success": False, "errors": errors})
            cotizaciones = TasaDeCambio.objects.all().order_by('-id')
            return render(request, "cotizaciones/lista.html", {
                "tasas": cotizaciones,
                "form": form,
                "show_modal": True,
                "obj_id": cotizacion.id, 
                "modal_type": "edit",
            })

    # GET → mostrar modal
    form = TasaDeCambioForm(instance=cotizacion)
    cotizaciones = TasaDeCambio.objects.all().order_by('-id')
    return render(request, "cotizaciones/lista.html", {
        "tasas": cotizaciones,
        "form": form,
        "show_modal": True,
        "modal_type": "edit",
        "obj_id": cotizacion.id,
    })

def cotizacion_desactivar(request, pk):
    """
    Vista que alterna el estado (activo/inactivo) de una cotización existente.

    - Busca la cotización por su ``pk``.
    - Cambia el valor de ``estado`` de True → False o False → True.
    - Guarda y redirige a ``cotizacion``.
    """
    cotizacion = get_object_or_404(TasaDeCambio, pk=pk)
    cotizacion.estado = not cotizacion.estado  # Alternar True/False
    cotizacion.save()
    return redirect("cotizacion")


def cotizacion_detalle(request, pk):
    """
    Vista que obtiene los datos de una cotización en formato JSON.

    - Usada para cargar datos en formularios de edición vía AJAX.
    - Devuelve:
        {
            "id": <id>,
            "moneda_origen": <id de moneda origen>,
            "moneda_destino": <id de moneda destino>,
            "monto_compra": <decimal>,
            "monto_venta": <decimal>,
            "vigencia": <fecha en formato "YYYY-MM-DD HH:MM:SS">
        }
    """
    cotizacion = get_object_or_404(TasaDeCambio, pk=pk)
    print(cotizacion, flush=True)
    print(cotizacion.vigencia, flush=True)
    return JsonResponse({
        "id": cotizacion.id,
        "moneda_origen": cotizacion.moneda_origen.id if cotizacion.moneda_origen else None,
        "moneda_destino": cotizacion.moneda_destino.id if cotizacion.moneda_destino else None,
        "monto_compra": float(cotizacion.monto_compra),
        "monto_venta": float(cotizacion.monto_venta),
        "comision_compra": float(cotizacion.comision_compra),
        "comision_venta": float(cotizacion.comision_venta),
        "vigencia": cotizacion.vigencia.strftime("%Y-%m-%d %H:%M") if cotizacion.vigencia else None,
    })