from django.shortcuts import render
from django.http import JsonResponse
from decimal import Decimal
import json
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from monedas.models import Moneda
from notificaciones.models import NotificacionMoneda

def panel_alertas(request):
    monedas = Moneda.objects.filter(estado=True)
    notificaciones_usuario = NotificacionMoneda.objects.filter(user=request.user, activa=True)
    monedas_activas = [n.moneda.abreviacion for n in notificaciones_usuario]

    return render(request, "notificaciones/configuracionAlertas.html", {
        "monedas": monedas,
        "monedas_activas": monedas_activas
    })


def guardar_configuracion(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            monedas_config = data.get("monedas", [])
            notificaciones_activas = data.get("notificaciones", True)

            # SIEMPRE procesar el array de monedas individualmente
            for m in monedas_config:
                abreviacion = m.get("moneda")
                activa = m.get("activa", False)
                
                try:
                    moneda = Moneda.objects.get(abreviacion=abreviacion)
                    NotificacionMoneda.objects.update_or_create(
                        user=request.user,
                        moneda=moneda,
                        defaults={'activa': activa}
                    )
                except Moneda.DoesNotExist:
                    continue

            # Siempre asegurar que PYG esté activa
            try:
                guarani = Moneda.objects.get(abreviacion="PYG")
                NotificacionMoneda.objects.update_or_create(
                    user=request.user,
                    moneda=guarani,
                    defaults={'activa': True}
                )
            except Moneda.DoesNotExist:
                pass
                
            return JsonResponse({"status": "ok", "message": "Configuración guardada"})
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)

    return JsonResponse({"status": "error", "message": "Método no permitido"}, status=405)