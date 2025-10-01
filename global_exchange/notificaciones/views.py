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
            NotificacionMoneda.objects.filter(user=request.user).delete()

            for m in monedas_config:
                abreviacion = m.get("moneda")
                activa = m.get("activa", False)
                try:
                    moneda = Moneda.objects.get(abreviacion=abreviacion)
                    NotificacionMoneda.objects.create(
                        user=request.user,
                        moneda=moneda,
                        activa=activa
                    )
                except Moneda.DoesNotExist:
                    continue

            return JsonResponse({"status": "ok", "message": "Configuración guardada"})
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)

    return JsonResponse({"status": "error", "message": "Método no permitido"}, status=405)

def test_notificaciones(request):
    return render(request, "notificaciones/test_notificaciones.html")