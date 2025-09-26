"""
Views (operaciones):
- simulador_operaciones: Pantalla principal de conversión y creación preliminar de transacciones.
- obtener_clientes_usuario / set_cliente_operativo: Gestión de cliente operativo (segmentación / descuento).
- verificar_tasa / hora_servidor: Utilidades AJAX.
- enviar_transaccion_al_banco: Ejemplo de integración externa.
- obtener_metodos_pago / guardar_metodo_pago: Gestión simple de métodos de pago.
- guardar_transaccion / actualizar_estado_transaccion: Endpoints JSON CRUD básicos para Transaccion.

Nota:
Mantiene la lógica existente; se agregan docstrings y comentarios aclaratorios.
"""

from decimal import Decimal
from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from datetime import datetime
from operaciones.models import Transaccion
from monedas.models import Moneda
from cotizaciones.models import TasaDeCambio
from clientes.models import Cliente
from cliente_usuario.models import Usuario_Cliente
from django.utils.dateparse import parse_datetime
from django.utils.timezone import now
import requests
from metodos_pagos.models import MetodoPago
from django.views.decorators.csrf import csrf_exempt
import json
from django.utils import timezone
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required


@login_required
def simulador_operaciones(request):
    """
    Página principal del simulador / conversor.

    Flujo:
    1. Obtiene últimas 5 transacciones del usuario (para tabla y gráfico).
    2. Construye estructura data_por_moneda con histórico de tasas activas.
    3. Aplica segmentación (descuento) según cliente operativo.
    4. Si POST: procesa cálculo (venta o compra) y devuelve JSON (AJAX) o recarga con resultado.
    5. Devuelve contexto con tasas, transacciones, métricas y parámetros para front.

    Respuesta AJAX (cuando header x-requested-with = XMLHttpRequest):
        {
          resultado, ganancia_total, segmento, descuento, tasa, fecha_tasa
        }

    Campos clave en context:
        - data_por_moneda: dict[abreviacion] -> lista cronológica de tasas (más antiguo al final).
        - transacciones: queryset últimas 5.
        - data_transacciones_json: JSON para Chart.js.
    """
    # === Transacciones dinámicas: últimas 5 del usuario ===
    transacciones_qs = Transaccion.ultimas(limite=5, usuario=request.user)\
        .select_related("moneda_origen", "moneda_destino")

    # Para el gráfico (orden cronológico ascendente)
    transacciones_chart = [
        {
            "dia": timezone.localtime(t.fecha).strftime("%d/%m"),
            "tipo": t.get_tipo_display(),  # "Compra"/"Venta"
            "monto": float(t.monto),
        }
        for t in reversed(list(transacciones_qs))
    ]

    # === Monedas activas desde la BD ===
    monedas = list(Moneda.objects.filter(estado=True).values("id", "abreviacion", "nombre"))

    # === Tasas de cambio activas (ordenadas: agrupadas por destino y descendente por vigencia) ===
    tasas = (
        TasaDeCambio.objects
        .filter(estado=True)
        .select_related("moneda_origen", "moneda_destino")
        .order_by("moneda_destino", "-vigencia")
    )

    metodos_pago = list(MetodoPago.objects.filter(activo=True).values("id", "nombre", "descripcion"))

    # Reorganizar tasas
    data_por_moneda = {}
    for tasa in tasas:
        abrev = tasa.moneda_destino.abreviacion
        if abrev not in data_por_moneda:
            data_por_moneda[abrev] = []
        # Insertar al inicio para mantener el más reciente al final (coherente con uso registros[-1])
        data_por_moneda[abrev].insert(0, {
            "id": tasa.id,
            "fecha": tasa.vigencia.strftime("%d %b"),
            "compra": float(tasa.monto_compra),
            "venta": float(tasa.monto_venta)
        })

    # Parámetros fijos / comisiones
    COMISION_VTA = 100
    COMISION_COM = 50

    # === Segmentación según usuario ===
    descuento = 0
    segmento_nombre = "Sin segmentación"
    clientes_asociados, cliente_operativo, email_cliente_operativo = obtener_clientes_usuario(request.user, request)

    if cliente_operativo and cliente_operativo.segmentacion and cliente_operativo.segmentacion.estado == "activo":
        descuento = float(cliente_operativo.segmentacion.descuento or 0)
        segmento_nombre = cliente_operativo.segmentacion.nombre

    # Variables iniciales de operación
    resultado = ""
    ganancia_total = 0
    valor_input = ""
    moneda_seleccionada = ""
    operacion = "venta"  # default
    origen = ""
    destino = ""
    TC_VTA = 0
    TC_COMP = 0
    PB_MONEDA = 0
    TASA_REF_ID = None

    # === Determinar tasa por defecto (primer moneda != PYG que tenga registros) ===
    tasa_default = None
    for abrev, registros in data_por_moneda.items():
        if abrev != "PYG" and registros:
            tasa_default = registros[-1]  # último = más reciente según construcción
            break

    if tasa_default:
        PB_MONEDA = tasa_default["venta"] if operacion == "venta" else tasa_default["compra"]
        TASA_REF_ID = tasa_default["id"]
        TC_VTA = PB_MONEDA + COMISION_VTA - (COMISION_VTA * descuento / 100)
        TC_COMP = PB_MONEDA - (COMISION_COM - (COMISION_COM * descuento / 100))
    else:
        TC_VTA = 0
        TC_COMP = 0

    # Procesar cálculo (AJAX / POST)
    if request.method == "POST":
        valor_input = request.POST.get("valor", "").strip()
        operacion = request.POST.get("operacion")
        origen = request.POST.get("origen", "")
        destino = request.POST.get("destino", "")

        # Validaciones básicas
        if origen == destino:
            return JsonResponse({"error": "La moneda de origen y destino no puede ser la misma."}, status=400)
        if operacion == "venta" and destino == "PYG":
            return JsonResponse({"error": "No puedes Comprar hacia Guaraní."}, status=400)
        if operacion == "compra" and origen == "PYG":
            return JsonResponse({"error": "No puedes Vender usando Guaraní como moneda de origen."}, status=400)

        # Selección según tipo de operación
        moneda_seleccionada = destino if operacion == "venta" else origen

        try:
            valor = float(valor_input)
            if valor <= 0:
                resultado = "Monto inválido"
            else:
                registros = data_por_moneda.get(moneda_seleccionada, [])
                if not registros:
                    resultado = "No hay cotización disponible"
                    ganancia_total = 0
                else:
                    ultimo = registros[-1]
                    PB_MONEDA = ultimo["venta"] if operacion == "venta" else ultimo["compra"]
                    TASA_REF_ID = ultimo["id"]

                    # Cálculos:
                    if operacion == "venta":
                        # Cliente entrega PYG, convertimos a moneda extranjera
                        TC_VTA = PB_MONEDA + COMISION_VTA - (COMISION_VTA * descuento / 100)
                        resultado = round(valor / TC_VTA, 2)
                        ganancia_total = round(valor - (resultado * PB_MONEDA), 2)
                    else:
                        # Cliente entrega moneda extranjera, recibe PYG
                        TC_COMP = PB_MONEDA - (COMISION_COM - (COMISION_COM * descuento / 100))
                        resultado = round(valor * TC_COMP, 2)
                        ganancia_total = round(valor * (COMISION_COM * (1 - descuento / 100)), 2)
        except ValueError:
            resultado = "Monto inválido"

    # Determinar tasa usada para respuesta
    tasa_usada = TC_VTA if operacion == "venta" else TC_COMP

    # Respuesta AJAX (cálculo dinámico)
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        # 'ultimo' puede no existir si nunca hubo registros
        fecha_tasa = locals().get("ultimo", {}).get("fecha", "")
        return JsonResponse({
            "resultado": resultado,
            "ganancia_total": ganancia_total,
            "segmento": segmento_nombre,
            "descuento": descuento,
            "tasa": tasa_usada,
            "fecha_tasa": fecha_tasa
        })

    context = {
        'monedas': monedas,
        'resultado': resultado,
        'ganancia_total': ganancia_total,
        'valor_input': valor_input,
        'moneda_seleccionada': moneda_seleccionada,
        'operacion': operacion,
        "user": request.user,
        "origen": origen,
        "destino": destino,
        'data_por_moneda': data_por_moneda,
        "segmento": segmento_nombre,
        "descuento": descuento,
        "clientes_asociados": clientes_asociados,
        "cliente_operativo": cliente_operativo,
        "tasa_vta": TC_VTA,
        "tasa_cmp": TC_COMP,
        "transacciones": transacciones_qs,
        "email_cliente_operativo": email_cliente_operativo,
        'medios': metodos_pago,
        "PB_MONEDA": PB_MONEDA,
        "TASA_REF_ID": TASA_REF_ID,
        "data_transacciones_json": json.dumps(transacciones_chart),
    }
    return render(request, 'operaciones/conversorReal.html', context)


def obtener_clientes_usuario(user, request):
    """
    Retorna (clientes_asociados, cliente_operativo, email_cliente_operativo).

    Lógica:
    - Busca asociaciones activas (Usuario_Cliente) con clientes activos.
    - Cliente operativo: el guardado en sesión o el primero disponible.
    """
    usuarios_clientes = (
        Usuario_Cliente.objects
        .select_related("id_cliente__segmentacion")
        .filter(id_usuario=user, id_cliente__estado="activo")
    )

    clientes_asociados = [uc.id_cliente for uc in usuarios_clientes if uc.id_cliente]
    cliente_operativo = None

    if request and request.session.get('cliente_operativo_id'):
        cliente_operativo = next((c for c in clientes_asociados if c.id == request.session['cliente_operativo_id']), None)
    if not cliente_operativo and clientes_asociados:
        cliente_operativo = clientes_asociados[0]

    email_cliente_operativo = cliente_operativo.email if cliente_operativo else ""
    return clientes_asociados, cliente_operativo, email_cliente_operativo


@login_required
def set_cliente_operativo(request):
    """
    POST:
        cliente_id
    Guarda en sesión el cliente operativo y devuelve datos de segmentación:
        { success, segmento, descuento, cliente_nombre, cliente_email }
    """
    cliente_id = request.POST.get('cliente_id')
    if cliente_id:
        try:
            cliente = Cliente.objects.select_related("segmentacion").get(
                pk=cliente_id, estado="activo"
            )
            request.session['cliente_operativo_id'] = cliente.id
            segmento_nombre = None
            descuento = 0
            if cliente.segmentacion and cliente.segmentacion.estado == "activo":
                segmento_nombre = cliente.segmentacion.nombre
                descuento = float(cliente.segmentacion.descuento or 0)
            return JsonResponse({
                "success": True,
                "segmento": segmento_nombre,
                "descuento": descuento,
                "cliente_nombre": cliente.nombre,
                "cliente_email": cliente.email
            })
        except Cliente.DoesNotExist:
            return JsonResponse({"success": False, "error": "Cliente no encontrado"}, status=404)
    return JsonResponse({"success": False, "error": "Petición inválida"}, status=400)


def verificar_tasa(request):
    """
    GET params: origen, destino
    Devuelve fecha_tasa de la última tasa disponible o error 404.
    """
    origen = request.GET.get("origen")
    destino = request.GET.get("destino")
    try:
        tasa = TasaDeCambio.objects.filter(
            moneda_origen__abreviacion=origen,
            moneda_destino__abreviacion=destino
        ).latest("fecha_actualizacion")
        return JsonResponse({"fecha_tasa": tasa.fecha_actualizacion.isoformat()})
    except TasaDeCambio.DoesNotExist:
        return JsonResponse({"error": "No hay tasa disponible"}, status=404)


def hora_servidor(request):
    """
    Devuelve hora actual del servidor (ISO 8601).
    """
    return JsonResponse({"hora": now().isoformat()})


def enviar_transaccion_al_banco(cliente_id, monto, moneda):
    """
    Ejemplo de integración externa (POST simple).
    Retorna JSON (o dict con 'error').
    """
    url = "http://localhost:8001/api/banco/transaccion/"
    data = {"cliente_id": cliente_id, "monto": monto, "moneda": moneda}
    try:
        response = requests.post(url, json=data, timeout=5)
        return response.json()
    except Exception as e:
        return {"error": str(e)}


def obtener_metodos_pago(request):
    """
    GET: lista métodos de pago activos.
    """
    if request.method == "GET":
        metodos = MetodoPago.objects.filter(activo=True).values("id", "nombre", "descripcion")
        return JsonResponse(list(metodos), safe=False)
    return JsonResponse({"error": "Método no permitido"}, status=405)


@csrf_exempt
def guardar_metodo_pago(request):
    """
    POST: metodo, detalle
    (Ejemplo de endpoint simple; no persiste detalle en DB en esta versión.)
    """
    if request.method == "POST":
        metodo_id = request.POST.get("metodo")
        detalle = request.POST.get("detalle")
        return JsonResponse({"status": "ok", "metodo": metodo_id, "detalle": detalle})
    return JsonResponse({"error": "Método no válido"}, status=400)


def guardar_transaccion(request):
    """
    POST (JSON):
        {
          monto, tipo, estado?, moneda_origen_id, moneda_destino_id,
          tasa_usada, tasa_ref_id
        }
    Crea Transaccion y devuelve:
        { success, id, estado, fecha } o errores.
    """
    try:
        data = json.loads(request.body.decode("utf-8"))
    except Exception as e:
        return JsonResponse({"success": False, "error": "JSON inválido", "detail": str(e)}, status=400)

    try:
        usuario = request.user if request.user.is_authenticated else None
        monto = Decimal(str(data.get("monto", "0")))
        tipo = data.get("tipo")
        estado = data.get("estado", "pendiente").lower()
        moneda_origen_id = data.get("moneda_origen_id")
        moneda_destino_id = data.get("moneda_destino_id")
        tasa_usada = Decimal(str(data.get("tasa_usada", "0")))
        tasa_ref_id = data.get("tasa_ref_id")

        if not (moneda_origen_id and moneda_destino_id and tasa_ref_id):
            return JsonResponse({"success": False, "error": "Faltan campos obligatorios"}, status=400)

        moneda_origen = Moneda.objects.get(id=moneda_origen_id)
        moneda_destino = Moneda.objects.get(id=moneda_destino_id)
        tasa_ref = TasaDeCambio.objects.get(id=tasa_ref_id)

        transaccion = Transaccion.objects.create(
            usuario=usuario,
            monto=monto,
            tipo=tipo,
            estado=estado,
            moneda_origen=moneda_origen,
            moneda_destino=moneda_destino,
            tasa_usada=tasa_usada,
            tasa_ref=tasa_ref,
        )

        return JsonResponse({
            "success": True,
            "id": transaccion.id,
            "estado": transaccion.estado,
            "fecha": transaccion.fecha.strftime("%d/%m/%Y %H:%M"),
        })

    except Moneda.DoesNotExist:
        return JsonResponse({"success": False, "error": "Moneda no encontrada"}, status=404)
    except TasaDeCambio.DoesNotExist:
        return JsonResponse({"success": False, "error": "Tasa de cambio no encontrada"}, status=404)
    except Exception as e:
        return JsonResponse({"success": False, "error": "Error al guardar", "detail": str(e)}, status=500)


def actualizar_estado_transaccion(request):
    """
    POST (JSON):
        { transaccion_id, nuevo_estado }
    Actualiza estado y devuelve datos básicos.
    """
    if request.method == "POST":
        try:
            data = json.loads(request.body.decode("utf-8"))
            transaccion_id = data.get("transaccion_id")
            nuevo_estado = data.get("nuevo_estado")
            if not transaccion_id or not nuevo_estado:
                return JsonResponse({"success": False, "error": "Se requiere transaccion_id y nuevo_estado"}, status=400)

            transaccion = Transaccion.objects.get(id=transaccion_id)
            transaccion.estado = nuevo_estado
            transaccion.save()

            return JsonResponse({
                "success": True,
                "id": transaccion.id,
                "nuevo_estado": transaccion.estado,
                "fecha_actualizacion": transaccion.fecha.strftime("%d/%m/%Y %H:%M")
            })

        except Transaccion.DoesNotExist:
            return JsonResponse({"success": False, "error": "Transacción no encontrada"}, status=404)
        except Exception as e:
            return JsonResponse({"success": False, "error": "Error al actualizar", "detail": str(e)}, status=500)

    return JsonResponse({"success": False, "error": "Método no permitido"}, status=405)