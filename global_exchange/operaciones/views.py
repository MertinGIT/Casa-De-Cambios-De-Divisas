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
import os
from django.views.decorators.http import require_POST

from decimal import Decimal
from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from datetime import datetime
from medio_acreditacion.models import MedioAcreditacion
from operaciones.models import Transaccion
from monedas.models import Moneda
from cotizaciones.models import TasaDeCambio
from clientes.models import Cliente
from cliente_usuario.models import Usuario_Cliente
from django.utils.dateparse import parse_datetime
from django.utils.timezone import now, localtime
from datetime import timedelta
import requests
from metodos_pagos.models import MetodoPago
from django.views.decorators.csrf import csrf_exempt
import json
from django.utils import timezone
from django.http import JsonResponse
from limite_moneda.models import LimiteTransaccion
from django.db.models import Sum
import random
from django.core.mail import send_mail
import datetime


@login_required
def simulador_operaciones(request):
    """
    Simula operaciones de compra/venta de monedas.

    Obtiene las tasas de cambio activas, métodos de pago disponibles,
    y datos de clientes asociados al usuario para calcular resultados
    de transacciones con comisiones y posibles descuentos por segmentación.

    :param request: Objeto HTTP con información de la petición.
    :type request: HttpRequest
    :return: Página renderizada con contexto de simulación o JsonResponse si es AJAX.
    :rtype: HttpResponse | JsonResponse
    """

    # === Monedas activas desde la BD ===
    monedas = list(Moneda.objects.filter(estado=True).values("id", "abreviacion", "nombre"))
    
    # === Transacciones dinámicas: últimas 5 del usuario ===
    transacciones_qs = Transaccion.ultimas(limite=5, usuario=request.user)\
        .select_related("moneda_origen", "moneda_destino")

    # Para el gráfico (orden cronológico ascendente)
    transacciones_chart = [
        {
            "dia": timezone.localtime(t.fecha).strftime("%d/%m"),
            "tipo": t.get_tipo_display(),  # "Compra"/"Venta"
            "monto": float(t.monto),
            "estado":t.estado,
            "moneda": t.moneda_origen.abreviacion if t.tipo == 'Compra' else t.moneda_destino.abreviacion
        }
        for t in reversed(list(transacciones_qs))
    ]

    

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
            "comision_compra": float(tasa.comision_compra),
            "comision_venta": float(tasa.comision_venta),
            "precio_base": float(tasa.precio_base)
        })
        
    print("data_por_monedaaaaaaaaaa:", data_por_moneda,flush=True)
    # Comisiones y variables
    COMISION_VTA = 0
    COMISION_COM = 0

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
    TASA_REF_ID =None
    resultado_sin_desc=0
    limites = LimiteTransaccion.objects.all()  # tus límites generales por moneda

    hoy = localtime(now()).date()
    #hoy=datetime.date(2025, 10, 5)
    inicio_mes = hoy.replace(day=1)

    limites_disponibles = []

    for limite in limites:
        # Filtrar transacciones confirmadas y no canceladas
        transacciones_validas = Transaccion.objects.filter(
            estado__in=["completada"]  # solo considerar transacciones activas
        )

        # Gastado hoy
        gasto_diario = transacciones_validas.filter(
            fecha__date=hoy
        ).aggregate(total=Sum("monto"))["total"] or 0

        # Gastado en el mes
        gasto_mensual = transacciones_validas.filter(
            fecha__date__gte=inicio_mes
        ).aggregate(total=Sum("monto"))["total"] or 0

        limites_disponibles.append({
            "limite": limite,
            "gasto_diario": gasto_diario,
            "disponible_diario": max(limite.limite_diario - gasto_diario, 0),
            "gasto_mensual": gasto_mensual,
            "disponible_mensual": max(limite.limite_mensual - gasto_mensual, 0),
        })

        
    # === Determinar tasas por defecto para mostrar en GET ===
    tasa_default = None
    for abrev, registros in data_por_moneda.items():
        if abrev != "PYG" and registros:
            tasa_default = registros[-1]  # último = más reciente según construcción
            break
    
    print("tasa_default:", tasa_default,flush=True)

    if tasa_default:
        COMISION_VTA = tasa_default.get("comision_venta", 0)
        COMISION_COM = tasa_default.get("comision_compra", 0)
        # antes usabas venta/compra según operacion, ahora usamos precio_base siempre
        PB_MONEDA = tasa_default.get("precio_base", 0)
        #PB_MONEDA = tasa_default["venta"] if operacion == "venta" else tasa_default["compra"]
        TASA_REF_ID = tasa_default["id"]

        TC_VTA = PB_MONEDA + COMISION_VTA - (COMISION_VTA * descuento / 100)
        TC_COMP = PB_MONEDA - (COMISION_COM - (COMISION_COM * descuento / 100))
        print("PB_MONEDA de if tasa_default:",PB_MONEDA, flush=True)
        print("TC_VTA de if tasa_default:",TC_VTA, flush=True)
        print("TC_COMP de if tasa_default:",TC_COMP, flush=True)
        print("COMISION_VTA de if tasa_default:",COMISION_VTA, flush=True)
        print("COMISION_COM de if tasa_default:",COMISION_COM, flush=True)
    else:
        TC_VTA = 0
        TC_COMP = 0

    print("TC_VTA de simulacion de operaciones:",TC_VTA, flush=True)
    print("TC_COMP de simulacion de operaciones:",TC_COMP ,flush=True)   

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
                    COMISION_VTA = ultimo.get("comision_venta", 0)
                    COMISION_COM = ultimo.get("comision_compra", 0)
                    # ahora leemos precio_base directamente
                    PB_MONEDA = tasa_default.get("precio_base", 0)
                    #PB_MONEDA = ultimo["venta"] if operacion == "venta" else ultimo["compra"]
                    TASA_REF_ID = ultimo["id"]
                    print("entra en el else de simulacion de operaciones:", flush=True)
                    print("PB_MONEDA del else:",PB_MONEDA, flush=True)
                    # Cálculos:
                    if operacion == "venta":
                        # Cliente entrega PYG, convertimos a moneda extranjera
                        TC_VTA = PB_MONEDA + COMISION_VTA - (COMISION_VTA * descuento / 100)
                        TC_VTA_SIN_DESC = PB_MONEDA + COMISION_VTA  # sin beneficio
                        resultado_sin_desc = round(valor / TC_VTA_SIN_DESC, 2)
                        resultado = round(valor / TC_VTA, 2)
                        ganancia_total = round(valor - (resultado * PB_MONEDA), 2)
                    else:
                        # Cliente entrega moneda extranjera, recibe PYG
                        TC_COMP = PB_MONEDA - (COMISION_COM - (COMISION_COM * descuento / 100))
                        TC_COMP_SIN_DESC = PB_MONEDA - COMISION_COM  # sin beneficio
                        resultado_sin_desc = round(valor * TC_COMP_SIN_DESC, 2)
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
            "resultado_sin_desc": resultado_sin_desc,  # sin descuento
            "ganancia_total": ganancia_total,
            "segmento": segmento_nombre,
            "descuento": descuento,
            "tasa": tasa_usada,
            "fecha_tasa": fecha_tasa
        })
    print("TC_VTA: ", TC_VTA,flush=True)
    print("clientes_asociados: ",clientes_asociados,flush=True)
    print("cliente_operativo: ",cliente_operativo,flush=True)
    print("TC_VTA 222: ",TC_VTA,flush=True)
    print("TC_COMP222: ",TC_COMP,flush=True)


    # Obtener medios de acreditación del cliente operativo
    medios_acreditacion = []
    if cliente_operativo:
        medios_qs = MedioAcreditacion.objects.filter(cliente=cliente_operativo, estado=True)
        for m in medios_qs:
            medios_acreditacion.append({
                "id": m.id,
                "entidad": {
                    "nombre": m.entidad.nombre,
                    "tipo": m.entidad.tipo,
                },
                "tipo_cuenta": m.tipo_cuenta,
                "numero_cuenta": m.numero_cuenta,
                "titular": m.titular,
                "documento_titular": m.documento_titular,
                "moneda": {
                    "nombre": m.moneda.nombre,
                    "abreviacion": m.moneda.abreviacion,
                },
                "tiempo_acreditacion": "2-3 minutos"  # si lo querés fijo por ahora
            })
        print("medios_acreditacion:", medios_acreditacion, flush=True)
        
    print("context resultado",resultado)
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
        "cliente_operativo_id": cliente_operativo.id if cliente_operativo else None,
        "tasa_vta": TC_VTA,
        "tasa_cmp": TC_COMP,
        "transacciones": transacciones_qs,
        "email_cliente_operativo": email_cliente_operativo,
        'medios': metodos_pago,
        "PB_MONEDA": PB_MONEDA,
        "TASA_REF_ID": TASA_REF_ID,
        "data_transacciones_json": json.dumps(transacciones_chart),  # para el gráfico
        "medios_acreditacion": json.dumps(medios_acreditacion),
        "limites_cliente": limites_disponibles,
    }

    return render(request, 'operaciones/conversorReal.html', context)


@require_POST
def verificar_limites(request):
    """
    Verifica si el monto de la transacción excede los límites diarios o mensuales
    """
    try:
        monto = Decimal(request.POST.get('monto', 0))
        moneda_abrev = request.POST.get('moneda')
        
        # Obtener la moneda
        moneda = Moneda.objects.get(abreviacion=moneda_abrev)
        
        # Obtener el límite general para esta moneda
        limite = LimiteTransaccion.objects.filter(moneda_id=1).first()
        
        if not limite:
            return JsonResponse({
                'success': False,
                'mensaje': f'No se encontró límite configurado para {moneda_abrev}'
            })
        
        # Obtener límites configurados
        limite_diario = limite.limite_diario
        limite_mensual = limite.limite_mensual
        
        # Calcular fechas
        hoy = localtime(now()).date()
        #hoy=datetime.date(2025, 10, 7)
        inicio_mes = hoy.replace(day=1)
        print("hoy:",hoy,flush=True)
        print("inicio_mes:",inicio_mes,flush=True)
        
        # Filtrar solo transacciones completadas
        transacciones_validas = Transaccion.objects.filter(
            estado__in=["completada"]  # solo considerar transacciones completadas
        )
        
        # Calcular gasto diario
        gasto_diario = transacciones_validas.filter(
            fecha__date=hoy
        ).aggregate(total=Sum("monto"))["total"] or Decimal('0')
        
        # Calcular gasto mensual
        gasto_mensual = transacciones_validas.filter(
            fecha__date__gte=inicio_mes
        ).aggregate(total=Sum("monto"))["total"] or Decimal('0')
        
        # Calcular disponibles
        disponible_diario = limite_diario - gasto_diario
        disponible_mensual = limite_mensual - gasto_mensual
        
        # Verificar si excede límites
        excede_diario = monto > disponible_diario
        excede_mensual = monto > disponible_mensual
        
        # Formatear números para mostrar (formato paraguayo: 1.234.567,89)
        def format_number(num):
            num_str = f"{float(num):,.2f}"
            # Cambiar formato americano a paraguayo
            num_str = num_str.replace(',', 'X').replace('.', ',').replace('X', '.')
            return num_str
        
        return JsonResponse({
            'success': True,
            'excede_diario': excede_diario,
            'excede_mensual': excede_mensual,
            'moneda': moneda_abrev,
            'monto_solicitado': format_number(monto),
            'limite_diario': format_number(limite_diario),
            'gastado_diario': format_number(gasto_diario),
            'disponible_diario': format_number(disponible_diario),
            'limite_mensual': format_number(limite_mensual),
            'gastado_mensual': format_number(gasto_mensual),
            'disponible_mensual': format_number(disponible_mensual)
        })
        
    except Moneda.DoesNotExist:
        return JsonResponse({
            'success': False,
            'mensaje': f'Moneda {moneda_abrev} no encontrada'
        })
    except Exception as e:
        print(f"Error en verificar_limites: {str(e)}", flush=True)
        return JsonResponse({
            'success': False,
            'mensaje': f'Error al verificar límites: {str(e)}'
        })

def obtener_clientes_usuario(user,request):
    """
    Obtiene los clientes asociados a un usuario y determina cuál es el cliente operativo.

    :param user: Usuario autenticado.
    :type user: User
    :param request: Objeto HTTP con información de la petición (usado para sesión).
    :type request: HttpRequest
    :return: Tupla con (lista de clientes asociados, cliente operativo actual, email del cliente operativo).
    :rtype: tuple[list[Cliente], Cliente | None, str]
    """

    # Solo clientes activos
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
    Establece en sesión el cliente operativo para el usuario autenticado.

    Permite cambiar el cliente activo en el contexto de las operaciones.
    Devuelve información de segmentación y descuento del cliente seleccionado.

    :param request: Objeto HTTP con la información de la petición.
    :type request: HttpRequest
    :return: JsonResponse con los datos del cliente operativo o error.
    :rtype: JsonResponse
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
    Verifica la tasa de cambio entre dos monedas.

    Devuelve la última tasa registrada entre el origen y destino,
    junto con su fecha de actualización.

    :param request: Objeto HTTP con los parámetros "origen" y "destino".
    :type request: HttpRequest
    :return: JsonResponse con fecha de la tasa o error si no existe.
    :rtype: JsonResponse
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
    Devuelve la hora actual del servidor.

    :param request: Objeto HTTP.
    :type request: HttpRequest
    :return: JsonResponse con la hora ISO.
    :rtype: JsonResponse
    """
    return JsonResponse({"hora": now().isoformat()})    


def enviar_transaccion_al_banco(cliente_id, monto, moneda):
    """
    Envía una transacción al servicio bancario externo.

    :param cliente_id: ID del cliente.
    :type cliente_id: int
    :param monto: Monto de la transacción.
    :type monto: Decimal | float
    :param moneda: Abreviación de la moneda.
    :type moneda: str
    :return: Respuesta en formato JSON del servicio bancario.
    :rtype: dict
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
    Devuelve la lista de métodos de pago activos.

    :param request: Objeto HTTP.
    :type request: HttpRequest
    :return: JsonResponse con la lista de métodos.
    :rtype: JsonResponse
    """
    if request.method == "GET":
        metodos = MetodoPago.objects.filter(activo=True).values("id", "nombre", "descripcion")
        return JsonResponse(list(metodos), safe=False)
    return JsonResponse({"error": "Método no permitido"}, status=405)


@csrf_exempt
def guardar_metodo_pago(request):
    """
    Guarda el método de pago seleccionado en una transacción.

    :param request: Objeto HTTP con datos "metodo" y "detalle".
    :type request: HttpRequest
    :return: JsonResponse con estado de la operación.
    :rtype: JsonResponse
    """
    if request.method == "POST":
        metodo_id = request.POST.get("metodo")
        detalle = request.POST.get("detalle")
        return JsonResponse({"status": "ok", "metodo": metodo_id, "detalle": detalle})
    return JsonResponse({"error": "Método no válido"}, status=400)


def guardar_transaccion(request):
    """
    Guarda una transacción en la base de datos.

    Recibe los datos en JSON: monto, tipo, monedas, tasa, estado y cliente.
    Asocia la transacción con el usuario autenticado y el cliente operativo.

    :param request: Objeto HTTP con los datos de la transacción.
    :type request: HttpRequest
    :return: JsonResponse con la información de la transacción guardada o error.
    :rtype: JsonResponse
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
        cliente_id = data.get("cliente_id")

        # Validación de campos obligatorios
        if not (moneda_origen_id and moneda_destino_id and tasa_ref_id and cliente_id):
            return JsonResponse({"success": False, "error": "Faltan campos obligatorios (incluye cliente_id)"}, status=400)

        # Obtener instancias de los modelos
        moneda_origen = Moneda.objects.get(id=moneda_origen_id)
        moneda_destino = Moneda.objects.get(id=moneda_destino_id)
        tasa_ref = TasaDeCambio.objects.get(id=tasa_ref_id)
        cliente = Cliente.objects.get(id=cliente_id, estado="activo")

        # Validar que el cliente pertenece al usuario
        if usuario:
            relacion = Usuario_Cliente.objects.filter(
                id_usuario=usuario, 
                id_cliente=cliente
            ).exists()
            if not relacion:
                return JsonResponse({
                    "success": False, 
                    "error": "El cliente no está asociado al usuario"
                }, status=403)

        # Crear la transacción
        transaccion = Transaccion.objects.create(
            usuario=usuario,
            monto=monto,
            tipo=tipo,
            estado=estado,
            moneda_origen=moneda_origen,
            moneda_destino=moneda_destino,
            tasa_usada=tasa_usada,
            tasa_ref=tasa_ref,
            cliente=cliente,
        )

        return JsonResponse({
            "success": True,
            "id": transaccion.id,
            "estado": transaccion.estado,
            "fecha": transaccion.fecha.strftime("%d/%m/%Y %H:%M"),
            "cliente_nombre": cliente.nombre,
        })

    except Moneda.DoesNotExist:
        return JsonResponse({"success": False, "error": "Moneda no encontrada"}, status=404)
    except TasaDeCambio.DoesNotExist:
        return JsonResponse({"success": False, "error": "Tasa de cambio no encontrada"}, status=404)
    except Cliente.DoesNotExist:
        return JsonResponse({"success": False, "error": "Cliente no encontrado o inactivo"}, status=404)
    except Exception as e:
        return JsonResponse({"success": False, "error": "Error al guardar", "detail": str(e)}, status=500)


def actualizar_estado_transaccion(request):


    """
    Actualiza el estado de una transacción existente.

    Recibe en JSON el ID de la transacción y el nuevo estado,
    luego lo guarda en la base de datos.

    :param request: Objeto HTTP con datos "transaccion_id" y "nuevo_estado".
    :type request: HttpRequest
    :return: JsonResponse con resultado de la actualización.
    :rtype: JsonResponse
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

import stripe

os.getenv("STRIPE_SECRET_KEY")
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
@csrf_exempt
def crear_pago_stripe(request):
    if request.method == "POST":
        try:
            total = int(request.POST.get("total", 0))
            moneda = "pyg"

            payment_intent = stripe.PaymentIntent.create(
                amount=total,
                currency=moneda,
                automatic_payment_methods={"enabled": True}
            )

            return JsonResponse({"client_secret": payment_intent.client_secret})

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
    return JsonResponse({"error": "Método no permitido"}, status=405)

def enviar_pin(request):
    if request.user.is_authenticated:
        # Generar un PIN aleatorio de 4 dígitos
        pin = str(random.randint(1000, 9999))

        # Guardar PIN en la sesión (válido por una transacción)
        request.session['pin_seguridad'] = pin

        # Enviar el PIN al email del usuario
        asunto = "Tu código PIN de verificación"
        mensaje = f"Hola {request.user.username},\n\nTu código de verificación es: {pin}\n\nEste código vence en unos minutos."
        remitente = None  # Usará EMAIL_HOST_USER por defecto
        destinatarios = [request.user.email]

        send_mail(asunto, mensaje, remitente, destinatarios)

        return JsonResponse({"success": True, "message": "Se envió un PIN a tu correo"})
    return JsonResponse({"success": False, "message": "Usuario no autenticado"})

def validar_pin(request):
    if request.method == "POST":
        pin_ingresado = request.POST.get("pin")
        pin_guardado = request.session.get("pin_seguridad")

        if pin_guardado and pin_ingresado == pin_guardado:
            # PIN válido, eliminarlo de la sesión para que no se reutilice
            del request.session['pin_seguridad']
            return JsonResponse({"success": True})
        else:
            return JsonResponse({"success": False, "message": "PIN incorrecto"})

