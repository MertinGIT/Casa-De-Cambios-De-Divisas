from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from operaciones.models import Transaccion
from django.utils import timezone
import json
import traceback

def safe_str(obj):
    """Convierte un objeto a string, maneja None y errores."""
    try:
        return str(obj) if obj is not None else "N/A"
    except Exception:
        return "N/A"

@login_required
def listar_transacciones(request):
    """
    Lista todas las transacciones con filtros opcionales.
    Retorna JSON para peticiones AJAX o renderiza template para GET normal.
    """
    
    if not request.user.is_staff:
        return JsonResponse({"error": "Acceso denegado"}, status=403)
    
    # Obtener todas las transacciones
    transacciones = Transaccion.objects.select_related(
        'usuario', 'cliente', 'moneda_origen', 'moneda_destino', 'metodo_pago'
    ).order_by('-fecha')
    
    # Aplicar filtros si existen
    cliente_nombre = request.GET.get('cliente_nombre', '').strip()
    estado = request.GET.get('estado', '').strip()
    metodo_pago = request.GET.get('metodo_pago', '').strip()
    usuario_nombre = request.GET.get('usuario', '').strip()
    transaccion_id = request.GET.get('id', '').strip()
    
    # Obtener el valor del input
    filtro_general = request.GET.get('filtro_cliente', '').strip()

    transacciones = Transaccion.objects.all()

    if filtro_general:
        transacciones = transacciones.filter(
            Q(cliente__nombre__icontains=filtro_general) |
            Q(usuario__username__icontains=filtro_general) |
            Q(id__icontains=filtro_general) |
            Q(tipo__icontains=filtro_general)
        )
    
    if estado:
        transacciones = transacciones.filter(estado=estado)
    
    if metodo_pago:
        transacciones = transacciones.filter(metodo_pago__nombre__icontains=metodo_pago)
    
    # Si es petición AJAX, devolver JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        transacciones_json = []
        for t in transacciones[:100]:
            try:
                transacciones_json.append({
                    "id": t.id,
                    "usuario": t.usuario.username if t.usuario else "N/A",
                    "cliente": safe_str(t.cliente),
                    "monto": float(t.monto) if t.monto else 0,
                    "tipo": t.tipo if t.tipo else "N/A",
                    "estado": t.estado if t.estado else "N/A",
                    "moneda_origen": safe_str(t.moneda_origen),
                    "moneda_destino": safe_str(t.moneda_destino),
                    "metodo_pago": safe_str(t.metodo_pago),
                    "ganancia": float(t.ganancia) if t.ganancia else 0,
                    "fecha": t.fecha.strftime('%d/%m/%Y %H:%M') if t.fecha else "",
                    "puede_procesar": t.estado == 'pendiente' and getattr(t.metodo_pago, 'nombre', None) == 'Efectivo'
                })
                print(f"✔ Transacción serializada: {t.id}", flush=True)
            except Exception as e:
                print(f"❌ Error serializando transacción {t.id}: {e}", flush=True)
                traceback.print_exc()
                continue
        print("JSON final:", transacciones_json, flush=True)
        return JsonResponse({"transacciones": transacciones_json})
    
    # Renderizar template para GET normal
    print("Transacciones GET normal:", transacciones[:100], flush=True)
    return render(request, 'admin_transacciones/admin_transacciones.html', {
        'transacciones': transacciones[:100],
        'total_transacciones': transacciones.count()
    })


@login_required
@csrf_exempt
def cambiar_estado_transaccion(request):
    """
    Cambia el estado de una transacción.
    Solo permite procesar transacciones en efectivo pendientes.
    """
    if request.method != 'POST':
        return JsonResponse({"success": False, "error": "Método no permitido"}, status=405)
    
    if not request.user.is_staff:
        return JsonResponse({"success": False, "error": "Acceso denegado"}, status=403)
    
    try:
        data = json.loads(request.body)
        transaccion_id = data.get('id')
        nuevo_estado = data.get('estado')
        
        if not transaccion_id or not nuevo_estado:
            return JsonResponse({"success": False, "error": "Faltan parámetros requeridos"}, status=400)
        
        transaccion = Transaccion.objects.select_related('cliente', 'metodo_pago').get(id=transaccion_id)
        
        if nuevo_estado == 'confirmada':
            transaccion.procesar(request.user)
            mensaje = "Transacción confirmada exitosamente"
        elif nuevo_estado == 'cancelada':
            transaccion.cancelar(request.user)
            mensaje = "Transacción cancelada exitosamente"
        else:
            return JsonResponse({"success": False, "error": "Estado no válido"}, status=400)
        
        print(f"✓ Transacción #{transaccion_id} {nuevo_estado} por {request.user.username}", flush=True)
        return JsonResponse({
            "success": True,
            "message": mensaje,
            "transaccion": {
                "id": transaccion.id,
                "estado": transaccion.estado,
                "fecha_procesado": transaccion.fecha_procesado.strftime('%d/%m/%Y %H:%M') if transaccion.fecha_procesado else None
            }
        })
        
    except Transaccion.DoesNotExist:
        return JsonResponse({"success": False, "error": "Transacción no encontrada"}, status=404)
    except ValueError as e:
        return JsonResponse({"success": False, "error": str(e)}, status=400)
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "Datos JSON inválidos"}, status=400)
    except Exception as e:
        print(f"❌ Error al cambiar estado: {str(e)}", flush=True)
        traceback.print_exc()
        return JsonResponse({"success": False, "error": f"Error interno: {str(e)}"}, status=500)


@login_required
def estadisticas_transacciones(request):
    """
    Retorna estadísticas de transacciones para el dashboard.
    """
    if not request.user.is_staff:
        return JsonResponse({"error": "Acceso denegado"}, status=403)
    
    from django.db.models import Sum
    
    stats = {
        "total": Transaccion.objects.count(),
        "pendientes": Transaccion.objects.filter(estado='pendiente').count(),
        "confirmadas": Transaccion.objects.filter(estado='confirmada').count(),
        "efectivo_pendiente": Transaccion.objects.filter(
            metodo_pago__nombre='Efectivo', 
            estado='pendiente'
        ).count(),
        "total_ganancia": Transaccion.objects.filter(
            estado='confirmada'
        ).aggregate(Sum('ganancia'))['ganancia__sum'] or 0
    }
    
    print("Estadísticas:", stats, flush=True)
    return JsonResponse(stats)
