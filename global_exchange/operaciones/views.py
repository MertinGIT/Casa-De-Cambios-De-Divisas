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
    Simula operaciones de compra/venta de monedas.

    Obtiene las tasas de cambio activas, métodos de pago disponibles,
    y datos de clientes asociados al usuario para calcular resultados
    de transacciones con comisiones y posibles descuentos por segmentación.

    :param request: Objeto HTTP con información de la petición.
    :type request: HttpRequest
    :return: Página renderizada con contexto de simulación o JsonResponse si es AJAX.
    :rtype: HttpResponse | JsonResponse
    """
    # === Datos de transacciones de prueba (estáticos) ===
    transacciones = [
      {"id": 1, "fecha": datetime.now().strftime("%d/%m/%Y %H:%M"), "monto": 1500.0, "estado": "Pendiente", "tipo": "Venta"},
      {"id": 2, "fecha": '18/07/2025 02:40' , "monto": 3200.0, "estado": "Completado", "tipo": "Compra"},
      {"id": 3, "fecha": '19/08/2024 05:40', "monto": 500.0, "estado": "Cancelado", "tipo": "Venta"},
  ]

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
    monedas = list(Moneda.objects.filter(estado=True).values("id","abreviacion", "nombre"))
    print("monedas: ",monedas,flush=True)
    # === Tasas de cambio activas ordenadas por vigencia más reciente ===
    tasas = (
        TasaDeCambio.objects
        .filter(estado=True)
        .select_related("moneda_origen", "moneda_destino")
        .order_by("moneda_destino", "-vigencia")
    )
    
    metodos_pago = list(MetodoPago.objects.filter(activo=True).values("id", "nombre", "descripcion"))
    print("metodos_pago: ",metodos_pago,flush=True)
    
    print("tasas 30: ",tasas,flush=True)

    # Reorganizar tasas en dict similar a tu data_por_moneda
    data_por_moneda = {}
    for tasa in tasas:
        abrev = tasa.moneda_destino.abreviacion
        if abrev not in data_por_moneda:
            data_por_moneda[abrev] = []
        data_por_moneda[abrev].insert(0, {
            "id": tasa.id,
            "fecha": tasa.vigencia.strftime("%d %b"),
            "compra": float(tasa.monto_compra),
            "venta": float(tasa.monto_venta),
            "comision_compra": float(tasa.comision_compra),
            "comision_venta": float(tasa.comision_venta)
        })
    print("data_por_moneda 43: ",data_por_moneda,flush=True)

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

    # Variables iniciales
    resultado = ""
    ganancia_total = 0
    valor_input = ""
    moneda_seleccionada = ""
    operacion = "venta"
    origen = ""
    destino = ""
    TC_VTA = 0
    TC_COMP = 0
    PB_MONEDA = 0
    TASA_REF_ID =None
    
    # === Determinar tasas por defecto para mostrar en GET ===
    tasa_default = None
    for abrev, registros in data_por_moneda.items():
        if abrev != "PYG" and registros:
            # Tomar el registro más reciente
            tasa_default = registros[-1]
            print("tasa_default:",tasa_default,flush=True)
            break
            
    if tasa_default:
        COMISION_VTA = tasa_default.get("comision_venta", 0)
        COMISION_COM = tasa_default.get("comision_compra", 0)
        PB_MONEDA = tasa_default["venta"] if operacion == "venta" else tasa_default["compra"]
        TASA_REF_ID = tasa_default["id"]
        # Calculamos las tasas considerando las comisiones
        TC_VTA = PB_MONEDA + COMISION_VTA - (COMISION_VTA * descuento / 100)
        TC_COMP = PB_MONEDA - (COMISION_COM - (COMISION_COM * descuento / 100))
        print("TC_VTA 88: ",TC_VTA,flush=True)
        print("TC_COMP 88: ",TC_COMP,flush=True)
    else:
        TC_VTA = 0
        TC_COMP = 0


    if request.method == "POST":
        valor_input = request.POST.get("valor", "").strip()
        operacion = request.POST.get("operacion")
        origen = request.POST.get("origen", "")
        destino = request.POST.get("destino", "")
        print("origen: ",origen,flush=True)
        print("destino: ",operacion,flush=True)

        print("operacion view 88: ",operacion,flush=True)

        # Validar que no sea la misma moneda
        if origen == destino:
            return JsonResponse({"error": "La moneda de origen y destino no puede ser la misma."}, status=400)

        # Validar que Guaraní solo esté donde corresponde
        if operacion == "venta" and destino == "PYG":
            return JsonResponse({"error": "No puedes Comprar hacia Guaraní."}, status=400)
        if operacion == "compra" and origen == "PYG":
            return JsonResponse({"error": "No puedes Vender usando Guaraní como moneda de origen."}, status=400)

        # Determinar moneda relevante según operación
        if operacion == "venta":
            moneda_seleccionada = destino
        else:
            moneda_seleccionada = origen
        

        try:
            valor = float(valor_input)
            print("entro try 105: ",operacion,flush=True)
            if valor <= 0:
                resultado = "Monto inválido"
            else:
                print("moneda_seleccionada 109: ",moneda_seleccionada,flush=True)
                print("data_por_moneda 110: ",data_por_moneda,flush=True)
                registros = data_por_moneda.get(moneda_seleccionada, [])
                print("registros 112: ",registros,flush=True)
                if not registros:
                    resultado = "No hay cotización disponible"
                    ganancia_total = 0
                else:
                    # Tomar el registro más reciente
                    ultimo = registros[-1]
                    COMISION_VTA = ultimo.get("comision_venta", 0)
                    COMISION_COM = ultimo.get("comision_compra", 0)
                    PB_MONEDA = ultimo["venta"] if operacion == "venta" else ultimo["compra"]
                    TASA_REF_ID = ultimo["id"]
                    # === Fórmula de tu home ===
                    #Venta es cuando el cliente compra moneda extranjera (entrega PYG),pero yo como admin le vendo la moneda extranjera
                    print("operacion: ", operacion, flush=True)
                    if operacion == "venta":
                        print("venta",flush=True)
                        print("Descuento: ",descuento,flush=True)
                        print("COMISION_VTA: ",COMISION_VTA,flush=True)
                        print("PB_MONEDA: ",PB_MONEDA,flush=True)
                        print("valor: ",valor,flush=True)
                        
                        TC_VTA = PB_MONEDA + COMISION_VTA - (COMISION_VTA * descuento / 100)
                        print("TC_VTA 138: ",TC_VTA,flush=True)
                        resultado = round(valor / TC_VTA, 2)
                        ganancia_total = round(valor - (resultado * PB_MONEDA), 2)
                        print("resultado 141: ",resultado,flush=True)
                        print("ganancia_total 142: ",ganancia_total,flush=True)
                    else:
                        print("PB_MONEDA16666666: ",PB_MONEDA,flush=True)
                        TC_COMP = PB_MONEDA - (COMISION_COM - (COMISION_COM * descuento / 100))
                        print("TC_COMP 1: ",TC_COMP,flush=True)
                        resultado = round(valor * TC_COMP, 2)
                        ganancia_total = round(valor * (COMISION_COM * (1 - descuento / 100)), 2)
                    print("resultado: ",resultado,flush=True)
        except ValueError:
            resultado = "Monto inválido"
    tasa_usada = 0
    
    if(operacion == "venta"):
        tasa_usada = TC_VTA
    else:
        tasa_usada = TC_COMP
    print("resultado 111: ",resultado,flush=True)
    # Respuesta AJAX
    print("tasa_usada.headers: ",tasa_usada,flush=True)
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            "resultado": resultado,
            "ganancia_total": ganancia_total,
            "segmento": segmento_nombre,
            "descuento": descuento,
            "tasa": tasa_usada,  
            "fecha_tasa": ultimo["fecha"]  # viene de tu dict data_por_moneda
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
                "tiempo_acreditacion": "1-2 horas"  # si lo querés fijo por ahora
            })
        print("medios_acreditacion:", medios_acreditacion, flush=True)
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
        "transacciones": transacciones_qs,  # para la tabla
        "email_cliente_operativo": email_cliente_operativo,
        'medios': metodos_pago,
        "PB_MONEDA": PB_MONEDA,
        "TASA_REF_ID": TASA_REF_ID,
        "data_transacciones_json": json.dumps(transacciones_chart),  # para el gráfico
        "medios_acreditacion": json.dumps(medios_acreditacion),
    }

    return render(request, 'operaciones/conversorReal.html', context)



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
    print("usuarios_clientes: ",usuarios_clientes,flush=True)
    # Tomar de la sesión si existe
    if request and request.session.get('cliente_operativo_id'):
        cliente_operativo = next((c for c in clientes_asociados if c.id == request.session['cliente_operativo_id']), None)

    # Si no hay sesión o ID no válido, tomar el primero
    if not cliente_operativo and clientes_asociados:
        cliente_operativo = clientes_asociados[0]

    # Obtener el email del cliente operativo
    email_cliente_operativo = cliente_operativo.email if cliente_operativo else ""
    print("email_operativo: ", email_cliente_operativo, flush=True)


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
            print("cliente:", cliente,flush=True)
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
                "cliente_nombre": cliente.nombre,
                "cliente_email": cliente.email
            })

        except Cliente.DoesNotExist:
            return JsonResponse(
                {"success": False, "error": "Cliente no encontrado"}, status=404
            )

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
        # Aseguramos que esté en formato ISO para JS
        fecha_iso = tasa.fecha_actualizacion.isoformat()
        return JsonResponse({"fecha_tasa": fecha_iso})
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
    data = {
        "cliente_id": cliente_id,
        "monto": monto,
        "moneda": moneda
    }
    response = requests.post(url, json=data)
    return response.json()

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
        # acá podés enlazar con la transacción
        print("Método elegido:", metodo_id, "Detalles:", detalle)
        return JsonResponse({"status": "ok"})
    return JsonResponse({"error": "Método no válido"}, status=400)

def guardar_transaccion(request):
    """
    Guarda una transacción en la base de datos.

    Recibe los datos en JSON: monto, tipo, monedas, tasa y estado.
    Asocia la transacción con el usuario autenticado si lo hay.

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

        # Recibir IDs directamente
        moneda_origen_id = data.get("moneda_origen_id")
        moneda_destino_id = data.get("moneda_destino_id")
        tasa_usada = Decimal(str(data.get("tasa_usada", "0")))
        tasa_ref_id = data.get("tasa_ref_id")

        if not (moneda_origen_id and moneda_destino_id and tasa_ref_id):
            return JsonResponse({"success": False, "error": "Faltan campos obligatorios"}, status=400)

        # Buscar por ID directamente
        moneda_origen = Moneda.objects.get(id=moneda_origen_id)
        moneda_destino = Moneda.objects.get(id=moneda_destino_id)
        tasa_ref = TasaDeCambio.objects.get(id=tasa_ref_id)

        # Guardar transacción
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
                return JsonResponse({
                    "success": False, 
                    "error": "Se requiere transaccion_id y nuevo_estado"
                }, status=400)
            
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
            return JsonResponse({
                "success": False, 
                "error": "Transacción no encontrada"
            }, status=404)
        except Exception as e:
            return JsonResponse({
                "success": False, 
                "error": "Error al actualizar", 
                "detail": str(e)
            }, status=500)
    
    return JsonResponse({"success": False, "error": "Método no permitido"}, status=405)
