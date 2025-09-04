from django.shortcuts import render, get_object_or_404, redirect
from clientes.models import Segmentacion
from functools import wraps
from .forms import SegmentacionForm
from django.http import JsonResponse
import json


def lista_segmentaciones(request):
    form = SegmentacionForm()
    segmentaciones = Segmentacion.objects.all()
    return render(request, "cliente_segmentacion/lista.html", {
        "segmentaciones": segmentaciones, 
        "form": form
    })

def crear_segmentacion(request):
    if request.method == "POST":
        form = SegmentacionForm(request.POST)
        
        # Verificar si es una petición AJAX
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        if form.is_valid():
            segmentacion = form.save()
            
            if is_ajax:
                # Respuesta AJAX exitosa
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
            else:
                # Redirección normal
                return redirect("lista-segmentaciones")
        else:
            if is_ajax:
                # Respuesta AJAX con errores
                return JsonResponse({
                    'success': False,
                    'errors': form.errors
                })
            else:
                # Renderizar template con errores
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
    Vista que permite editar una segmentación existente.
    Maneja tanto peticiones AJAX como peticiones normales.
    """
    segmentacion = get_object_or_404(Segmentacion, pk=pk)

    if request.method == "POST":
        form = SegmentacionForm(request.POST, instance=segmentacion)
        
        # Verificar si es una petición AJAX
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        if form.is_valid():
            segmentacion_actualizada = form.save()
            
            if is_ajax:
                # Respuesta AJAX exitosa
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
            else:
                # Redirección normal
                return redirect("lista-segmentaciones")
        else:
            if is_ajax:
                # Respuesta AJAX con errores
                return JsonResponse({
                    'success': False,
                    'errors': form.errors
                })
            else:
                # POST con errores: mostrar modal con errores
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
        # GET: abrir modal con form precargado
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
    segmentacion = get_object_or_404(Segmentacion, pk=pk)
    segmentacion.estado = "inactivo" if segmentacion.estado == "activo" else "activo"
    segmentacion.save()
    
    # Si es AJAX, devolver respuesta JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'nuevo_estado': segmentacion.estado,
            'message': f'Estado cambiado a {segmentacion.estado}'
        })
    
    return redirect("lista-segmentaciones")

def segmentacion_detalle(request, pk):
    """
    Vista que devuelve los detalles de una segmentación en formato JSON.
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