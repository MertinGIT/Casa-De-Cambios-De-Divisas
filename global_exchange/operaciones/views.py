from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from datetime import datetime
from monedas.models import Moneda
from cotizaciones.models import TasaDeCambio
from clientes.models import Cliente
from cliente_usuario.models import Usuario_Cliente

@login_required
def simulador_operaciones(request):
    # === Datos de transacciones de prueba (estáticos) ===
    transacciones = [
      {"id": 1, "fecha": datetime.now().strftime("%d/%m/%Y %H:%M"), "monto": 1500.0, "estado": "Pendiente", "tipo": "Venta"},
      {"id": 2, "fecha": '19/07/2025 02:40' , "monto": 3200.0, "estado": "Completado", "tipo": "Compra"},
      {"id": 3, "fecha": '19/08/2024 05:40', "monto": 500.0, "estado": "Cancelado", "tipo": "Venta"},
  ]

    # === Monedas activas desde la BD ===
    monedas = list(Moneda.objects.filter(estado=True).values("abreviacion", "nombre"))

    # === Tasas de cambio activas ordenadas por vigencia más reciente ===
    tasas = (
        TasaDeCambio.objects
        .filter(estado=True)
        .select_related("moneda_origen", "moneda_destino")
        .order_by("moneda_destino", "-vigencia")
    )

    # Reorganizar tasas en dict similar a tu data_por_moneda
    data_por_moneda = {}
    for tasa in tasas:
        abrev = tasa.moneda_destino.abreviacion
        if abrev not in data_por_moneda:
            data_por_moneda[abrev] = []
        data_por_moneda[abrev].insert(0, {
            "fecha": tasa.vigencia.strftime("%d %b"),
            "compra": float(tasa.monto_compra),
            "venta": float(tasa.monto_venta)
        })

    # Comisiones y variables
    COMISION_VTA = 100
    COMISION_COM = 50

    # === Segmentación según usuario ===
    descuento = 0
    segmento_nombre = "Sin segmentación"
    clientes_asociados, cliente_operativo = obtener_clientes_usuario(request.user, request)

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
    
    # === Determinar tasas por defecto para mostrar en GET ===
    tasa_default = None
    for abrev, registros in data_por_moneda.items():
        if abrev != "PYG" and registros:
            # Tomar el registro más reciente
            tasa_default = registros[0]
            break

    if tasa_default:
        # Calculamos las tasas considerando las comisiones
        TC_VTA = tasa_default["venta"] + COMISION_VTA
        TC_COMP = tasa_default["compra"] - COMISION_COM
    else:
        TC_VTA = 0
        TC_COMP = 0


    if request.method == "POST":
        valor_input = request.POST.get("valor", "").strip()
        operacion = request.POST.get("operacion")
        origen = request.POST.get("origen", "")
        destino = request.POST.get("destino", "")

        # Validar que no sea la misma moneda
        if origen == destino:
            return JsonResponse({"error": "La moneda de origen y destino no puede ser la misma."}, status=400)

        # Validar que Guaraní solo esté donde corresponde
        if operacion == "venta" and destino == "PYG":
            return JsonResponse({"error": "No puedes vender hacia Guaraní."}, status=400)
        if operacion == "compra" and origen == "PYG":
            return JsonResponse({"error": "No puedes comprar usando Guaraní como moneda de origen."}, status=400)

        # Determinar moneda relevante según operación
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
                    # Tomar el registro más reciente
                    ultimo = registros[0]
                    PB_MONEDA = ultimo["venta"] if operacion == "venta" else ultimo["compra"]

                    # === Fórmula de tu home ===
                    if operacion == "venta":
                        TC_VTA = PB_MONEDA + COMISION_VTA - (COMISION_VTA * descuento / 100)
                        resultado = round(valor / TC_VTA, 2)
                        ganancia_total = round(valor - (resultado * PB_MONEDA), 2)
                    else:
                        TC_COMP = PB_MONEDA - (COMISION_COM - (COMISION_COM * descuento / 100))
                        resultado = round(valor * TC_COMP, 2)
                        ganancia_total = round(valor * (COMISION_COM * (1 - descuento / 100)), 2)

        except ValueError:
            resultado = "Monto inválido"

        # Respuesta AJAX
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                "resultado": resultado,
                "ganancia_total": ganancia_total,
                "segmento": segmento_nombre,
                "descuento": descuento,
            })

    print("TC_VTA: ",TC_VTA,flush=True)
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
        "transacciones": transacciones,
        
    }

    return render(request, 'operaciones/conversorReal.html', context)




def obtener_clientes_usuario(user,request):
    """
    Devuelve:
        - clientes_asociados: lista de todos los clientes asociados al usuario
        - cliente_operativo: cliente actualmente seleccionado (desde sesión si existe)
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
    Guarda en sesión el cliente operativo seleccionado y devuelve JSON
    con segmento y descuento para actualizar el front sin recargar.
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