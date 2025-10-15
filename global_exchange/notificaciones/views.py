from django.shortcuts import render
from django.http import JsonResponse
from decimal import Decimal
import json
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from monedas.models import Moneda
from notificaciones.models import NotificacionMoneda
from cliente_usuario.models import Usuario_Cliente
from clientes.models import Cliente
from django.contrib.auth.decorators import login_required

def panel_alertas(request):
    """
    Muestra el panel de configuración de alertas para el usuario autenticado.

    Obtiene las monedas activas, las notificaciones configuradas por el usuario 
    y la información del cliente operativo actual (segmento y descuento).
    Retorna el contexto necesario para renderizar la plantilla 
    'notificaciones/configuracionAlertas.html'.
    """
    monedas = Moneda.objects.filter(estado=True)
    notificaciones_usuario = NotificacionMoneda.objects.filter(user=request.user, activa=True)
    monedas_activas = [n.moneda.abreviacion for n in notificaciones_usuario]
    
    segmento_nombre = "Sin Segmentación"
    descuento=0
    # === SEGMENTACIÓN SEGÚN USUARIO ===
    clientes_asociados, cliente_operativo = obtener_clientes_usuario(request.user,request)
    if cliente_operativo and cliente_operativo.segmentacion and cliente_operativo.segmentacion.estado == "activo":
        segmento_nombre = cliente_operativo.segmentacion.nombre
        if cliente_operativo.segmentacion.descuento:
            descuento = float(cliente_operativo.segmentacion.descuento)

    return render(request, "notificaciones/configuracionAlertas.html", {
        "monedas": monedas,
        "monedas_activas": monedas_activas,
        "segmento": segmento_nombre,
        "clientes_asociados": clientes_asociados,
        "cliente_operativo": cliente_operativo,'descuento': descuento
    })


def guardar_configuracion(request):
    """
    Procesa y guarda la configuración de alertas de monedas seleccionadas por el usuario.

    - Lee los datos enviados por POST en formato JSON.
    - Actualiza o crea los registros de notificación por moneda.
    - Asegura que la moneda base 'PYG' (Guaraní) siempre permanezca activa.
    - Devuelve una respuesta JSON con el estado de la operación.
    """
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


def obtener_clientes_usuario(user,request):
    """
    Obtiene los clientes asociados al usuario autenticado.

    Retorna:
        tuple:
            - clientes_asociados (list): Lista de instancias Cliente activas relacionadas con el usuario.
            - cliente_operativo (Cliente|None): Cliente actualmente seleccionado, 
              determinado a partir de la sesión o el primero disponible.
    """

     # Solo clientes activos
    usuarios_clientes = (
        Usuario_Cliente.objects
        .select_related("id_cliente__segmentacion")
        .filter(id_usuario=user, id_cliente__estado="activo")
    )
    
    clientes_asociados = [uc.id_cliente for uc in usuarios_clientes if uc.id_cliente]
    cliente_operativo = None

    # Tomar de la sesión si existe
    if request and request.session.get('cliente_operativo_id'):
        cliente_operativo = next((c for c in clientes_asociados if c.id == request.session['cliente_operativo_id']), None)

    # Si no hay sesión o ID no válido, tomar el primero
    if not cliente_operativo and clientes_asociados:
        cliente_operativo = clientes_asociados[0]

    return clientes_asociados, cliente_operativo


@login_required
def set_cliente_operativo(request):
    """
    Guarda en sesión el cliente operativo seleccionado y devuelve una respuesta JSON.

    Este endpoint permite actualizar dinámicamente la información de segmento y descuento
    del cliente activo en el frontend sin recargar la página.

    Retorna:
        JsonResponse:
            - success (bool): Indica si la operación fue exitosa.
            - segmento (str|None): Nombre del segmento activo (si existe).
            - descuento (float): Descuento asociado al segmento.
            - cliente_nombre (str): Nombre del cliente operativo seleccionado.
    """
    cliente_id = request.POST.get('cliente_id')

    if cliente_id:
        try:
            cliente = Cliente.objects.select_related("segmentacion").get(
                pk=cliente_id, estado="activo"
            )
            # Guardar en sesión
            request.session['cliente_operativo_id'] = cliente.id

            # Datos a devolver
            segmento_nombre = None
            descuento = 0
            if cliente.segmentacion and cliente.segmentacion.estado == "activo":
                segmento_nombre = cliente.segmentacion.nombre
                descuento = float(cliente.segmentacion.descuento or 0)

            return JsonResponse({
                "success": True,
                "segmento": segmento_nombre,
                "descuento": descuento,
                "cliente_nombre": cliente.nombre
            })

        except Cliente.DoesNotExist:
            return JsonResponse(
                {"success": False, "error": "Cliente no encontrado"}, status=404
            )

    return JsonResponse({"success": False, "error": "Petición inválida"}, status=400)
	