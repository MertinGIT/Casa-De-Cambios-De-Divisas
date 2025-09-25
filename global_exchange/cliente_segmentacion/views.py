from django.shortcuts import render, get_object_or_404, redirect
from clientes.models import Segmentacion
from functools import wraps
from .forms import SegmentacionForm
from django.http import JsonResponse


def check_nombre_segmentacion(request):
    """
    Verifica si el nombre de una segmentación ya existe en la base de datos.
    """
    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        obj_id = request.POST.get('obj_id')
        
        # Debug log para verificar parámetros recibidos
        print(f"🔍 DEBUG - check_nombre_segmentacion:")
        print(f"   - nombre: '{nombre}'")
        print(f"   - obj_id: '{obj_id}' (type: {type(obj_id)})")
        print(f"   - POST data: {dict(request.POST)}")

        if not nombre:
            print("❌ Nombre vacío, retornando False")
            return JsonResponse(False, safe=False)

        query = Segmentacion.objects.filter(nombre__iexact=nombre)
        print(f"🔎 Query inicial encontró: {query.count()} registros")

        # Si hay obj_id (edición), excluir ese registro
        if obj_id and obj_id != 'null' and obj_id != '' and obj_id != 'None':
            try:
                obj_id_int = int(obj_id)
                query_before = query.count()
                query = query.exclude(pk=obj_id_int)
                query_after = query.count()
                print(f"✅ Excluyendo registro con ID: {obj_id_int}")
                print(f"   - Registros antes de excluir: {query_before}")
                print(f"   - Registros después de excluir: {query_after}")
            except (ValueError, TypeError) as e:
                print(f"❌ Error al convertir obj_id a int: {obj_id} - Error: {e}")
        else:
            print(f"⚠️  No se excluyó ningún registro (obj_id: {obj_id})")

        exists = query.exists()
        is_valid = not exists
        
        print(f"📊 RESULTADO:")
        print(f"   - Query exists: {exists}")
        print(f"   - Is valid: {is_valid}")
        print(f"   - Retornando: {is_valid}")
        print("=" * 50)

        return JsonResponse(is_valid, safe=False)

    print("❌ Método no es POST")
    return JsonResponse(False, safe=False)

def lista_segmentaciones(request):
    """
    Muestra la lista de segmentaciones con búsqueda opcional.
    Permite filtrar por nombre o por segmentación.
    """
    form = SegmentacionForm()
    q = request.GET.get("q", "")
    campo = request.GET.get("campo", "")

    segmentaciones = Segmentacion.objects.all()

    if q and campo:
        if campo == "segmentacion":
            segmentaciones = segmentaciones.filter(nombre__icontains=q)
        # Por si hay necesidad de más filtros en el futuro
    return render(request, "cliente_segmentacion/lista.html", {
        "segmentaciones": segmentaciones, 
        "form": form,
        "q": q,
        "campo": campo,
    })

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

