from django.shortcuts import render, get_object_or_404, redirect
from clientes.models import Segmentacion
from functools import wraps
from .forms import SegmentacionForm
from django.http import JsonResponse

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
def lista_segmentaciones(request):
    form = SegmentacionForm()
    segmentaciones = Segmentacion.objects.all()
    return render(request, "cliente_segmentacion/lista.html", {
        "segmentaciones": segmentaciones, 
        "form": form
    })

@superadmin_required
def crear_segmentacion(request):
    if request.method == "POST":
        form = SegmentacionForm(request.POST)
        print(form)
        if form.is_valid():
            form.save()
            return redirect("lista-segmentaciones")
        else:
            segmentaciones = Segmentacion.objects.all()
            return render(request, "cliente_segmentacion/lista.html", {
                "segmentaciones": segmentaciones,
                "form": form,
                "show_modal": True,       # indica que se abra el modal
                "modal_type": "create",   # tipo de modal
            })
    return redirect("lista-segmentaciones")

@superadmin_required
def editar_segmentacion(request, pk):
    """
    Vista que permite editar una segmentación existente.

    Parámetros:
        - ``pk``: ID de la segmentación a editar.

    Flujo:
        - Si la petición es ``POST`` y el formulario es válido, guarda los cambios y redirige a ``lista-segmentaciones``.
        - Si hay errores de validación, recarga la lista de segmentaciones con el modal abierto mostrando los errores.
        - Si la petición es ``GET``, muestra la lista con el modal de edición precargado.

    Plantilla:
        - ``cliente_segmentacion/lista.html``
    """
    segmentacion = get_object_or_404(Segmentacion, pk=pk)

    if request.method == "POST":
        form = SegmentacionForm(request.POST, instance=segmentacion)
        if form.is_valid():
            form.save()
            return redirect("lista-segmentaciones")
        else:
            # POST con errores: mostrar modal con errores
            segmentaciones = Segmentacion.objects.all()
            return render(request, "cliente_segmentacion/lista.html", {
                "segmentaciones": segmentaciones,
                "form": form,
                "modal_title": "Editar Tipo de Cliente",
                "form_action": request.path,  # ← ESTO ES CLAVE
                "obj_id": segmentacion.id,
                "show_modal": True,
            })
    else:
        # GET: abrir modal con form precargado
        form = SegmentacionForm(instance=segmentacion)
        segmentaciones = Segmentacion.objects.all()  # ← NECESARIO PARA LA LISTA
        return render(request, "cliente_segmentacion/lista.html", {  # ← lista.html, NO form.html
            "segmentaciones": segmentaciones,
            "form": form,
            "modal_title": "Editar Tipo de Cliente",
            "form_action": request.path,  # ← ESTO ES CLAVE
            "obj_id": segmentacion.id,
            "show_modal": True,
        })


@superadmin_required
def cambiar_estado_segmentacion(request, pk):
    segmentacion = get_object_or_404(Segmentacion, pk=pk)
    segmentacion.estado = "inactivo" if segmentacion.estado == "activo" else "activo"
    segmentacion.save()
    return redirect("lista-segmentaciones")


def segmentacion_detalle(request, pk):
    segmentacion = get_object_or_404(Segmentacion, pk=pk)
    return JsonResponse({
        "nombre": segmentacion.nombre,
        "descripcion": segmentacion.descripcion,
        "descuento": segmentacion.descuento,
    })