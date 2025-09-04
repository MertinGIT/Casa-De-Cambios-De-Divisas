from django.shortcuts import render, get_object_or_404, redirect
from clientes.models import Segmentacion
from functools import wraps
from .forms import SegmentacionForm
from django.http import JsonResponse

def superadmin_required(view_func):
    """
    Decorador que restringe el acceso a vistas únicamente a superusuarios.

    Si el usuario no está autenticado, se redirige a 'login'.
    Si el usuario está autenticado pero no es superusuario, se redirige a 'home'.
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

def check_nombre_segmentacion(request):
    """
    Verifica si el nombre de una segmentación ya existe en la base de datos.

    Parámetros POST esperados:
        - nombre: str, nombre a validar.
        - obj_id: int o str, ID del objeto a excluir (en caso de edición).

    Retorna:
        JsonResponse con True si el nombre NO existe (válido) o False si ya está en uso.
    """
    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        obj_id = request.POST.get('obj_id')

        query = Segmentacion.objects.filter(nombre__iexact=nombre)

        # Si hay obj_id (edición), excluir ese registro
        if obj_id and obj_id != 'null' and obj_id != '':
            query = query.exclude(pk=obj_id)

        exists = query.exists()

        return JsonResponse(not exists, safe=False)

@superadmin_required
def lista_segmentaciones(request):
    """
    Muestra la lista de todas las segmentaciones existentes.

    Renderiza la plantilla 'cliente_segmentacion/lista.html' con:
        - segmentaciones: queryset de todas las segmentaciones.
        - form: formulario vacío para crear nueva segmentación.
    """
    form = SegmentacionForm()
    segmentaciones = Segmentacion.objects.all()
    return render(request, "cliente_segmentacion/lista.html", {
        "segmentaciones": segmentaciones, 
        "form": form
    })

@superadmin_required
def crear_segmentacion(request):
    """
    Crea una nueva segmentación.

    Soporta peticiones normales y AJAX. 
    - Si es AJAX, devuelve JsonResponse con éxito o errores.
    - Si no es AJAX, redirige a la lista o renderiza el modal con errores.
    """
    if request.method == "POST":
        form = SegmentacionForm(request.POST)
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        if form.is_valid():
            segmentacion = form.save()
            if is_ajax:
                return JsonResponse({
                    'success': True,
                    'message': 'Segmentación creada exitosamente',
                    'segmentacion': {
                        'id': segmentacion.id,
                        'nombre': segmentacion.nombre,
                        'descripcion': segmentacion.descripcion,
                        'descuento': float(segmentacion.descuento),
                        'estado': segmentacion.estado,
                    }
                })
            return redirect("lista-segmentaciones")
        else:
            if is_ajax:
                return JsonResponse({'success': False, 'errors': form.errors})
            segmentaciones = Segmentacion.objects.all()
            return render(request, "cliente_segmentacion/lista.html", {
                "segmentaciones": segmentaciones,
                "form": form,
                "show_modal": True,
                "modal_type": "create",
            })
    return redirect("lista-segmentaciones")

@superadmin_required
def editar_segmentacion(request, pk):
    """
    Edita una segmentación existente.

    Maneja peticiones GET para mostrar el modal con el formulario precargado
    y peticiones POST para actualizar la segmentación.

    Soporta AJAX y peticiones normales:
        - AJAX: devuelve JsonResponse con éxito o errores.
        - Normal: redirige a la lista o renderiza modal con errores.
    """
    segmentacion = get_object_or_404(Segmentacion, pk=pk)

    if request.method == "POST":
        form = SegmentacionForm(request.POST, instance=segmentacion)
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        if form.is_valid():
            segmentacion_actualizada = form.save()
            if is_ajax:
                return JsonResponse({
                    'success': True,
                    'message': 'Segmentación actualizada exitosamente',
                    'segmentacion': {
                        'id': segmentacion_actualizada.id,
                        'nombre': segmentacion_actualizada.nombre,
                        'descripcion': segmentacion_actualizada.descripcion,
                        'descuento': float(segmentacion_actualizada.descuento),
                        'estado': segmentacion_actualizada.estado,
                    }
                })
            return redirect("lista-segmentaciones")
        else:
            if is_ajax:
                return JsonResponse({'success': False, 'errors': form.errors})
            segmentaciones = Segmentacion.objects.all()
            return render(request, "cliente_segmentacion/lista.html", {
                "segmentaciones": segmentaciones,
                "form": form,
                "modal_title": "Editar Tipo de Cliente",
                "form_action": request.path,
                "modal_type": "edit", 
                "obj_id": segmentacion.id,
                "show_modal": True,
            })
    else:
        form = SegmentacionForm(instance=segmentacion)
        segmentaciones = Segmentacion.objects.all()
        return render(request, "cliente_segmentacion/lista.html", {
            "segmentaciones": segmentaciones,
            "form": form,
            "modal_title": "Editar Tipo de Cliente",
            "form_action": request.path,
            "obj_id": segmentacion.id,
            "show_modal": True,
            "modal_type": "edit",
        })

@superadmin_required
def cambiar_estado_segmentacion(request, pk):
    """
    Cambia el estado de una segmentación entre 'activo' e 'inactivo'.

    Si la petición es AJAX, devuelve JsonResponse con el nuevo estado.
    """
    segmentacion = get_object_or_404(Segmentacion, pk=pk)
    segmentacion.estado = "inactivo" if segmentacion.estado == "activo" else "activo"
    segmentacion.save()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'nuevo_estado': segmentacion.estado,
            'message': f'Estado cambiado a {segmentacion.estado}'
        })
    
    return redirect("lista-segmentaciones")

def segmentacion_detalle(request, pk):
    """
    Devuelve los detalles de una segmentación en formato JSON.

    Útil para cargar datos en modales de edición.
    """
    segmentacion = get_object_or_404(Segmentacion, pk=pk)
    return JsonResponse({
        "id": segmentacion.id,
        "nombre": segmentacion.nombre,
        "descripcion": segmentacion.descripcion,
        "descuento": float(segmentacion.descuento),
        "estado": segmentacion.estado,
    })
