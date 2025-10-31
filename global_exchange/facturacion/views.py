from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, FileResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
import json
from django.db.models import Q
from cliente_usuario.models import Usuario_Cliente
from .services import FacturaSeguraService
from .models import Factura, RangoFacturacion
from operaciones.models import Transaccion
from clientes.models import Cliente


@login_required
def facturacion_view(request):
    """
    Muestra el listado de **facturas electrónicas emitidas por el usuario actual**.

    Permite aplicar filtros por cliente, CDC, estado, fechas y transacción.  
    También calcula estadísticas por estado (aprobadas, pendientes, rechazadas)
    y detecta la **segmentación activa** del cliente operativo.

    **Parámetros:**

    - **request (HttpRequest):**  
      Solicitud HTTP con los filtros de búsqueda.

    **Retorna:**

    - **HttpResponse:**  
      Página HTML con la lista filtrada de facturas y sus métricas.
    """
    facturas = Factura.objects.filter(creado_por=request.user).select_related(
        'transaccion', 'cliente', 'rango_utilizado'
    )
    
    # Filtros
    busqueda = request.GET.get('busqueda', '').strip()
    if busqueda:
        facturas = facturas.filter(
            Q(cliente__nombre__icontains=busqueda) |
            Q(cliente__cedula__icontains=busqueda) |
            Q(cdc__icontains=busqueda) |
            Q(numero__icontains=busqueda)
        )
    
    estado = request.GET.get('estado', '').strip()
    if estado:
        facturas = facturas.filter(estado=estado)
    
    cliente = request.GET.get('cliente', '').strip()
    if cliente:
        facturas = facturas.filter(cliente__nombre__icontains=cliente)
    
    cdc = request.GET.get('cdc', '').strip()
    if cdc:
        facturas = facturas.filter(cdc__icontains=cdc)
    
    fecha_desde = request.GET.get('fecha_desde', '').strip()
    fecha_hasta = request.GET.get('fecha_hasta', '').strip()
    
    if fecha_desde:
        facturas = facturas.filter(fecha_emision__date__gte=fecha_desde)
    if fecha_hasta:
        facturas = facturas.filter(fecha_emision__date__lte=fecha_hasta)
    
    transaccion_id = request.GET.get('transaccion_id', '').strip()
    if transaccion_id:
        try:
            transaccion_id = int(transaccion_id)
            facturas = facturas.filter(transaccion_id=transaccion_id)
        except ValueError:
            pass
    
    facturas = facturas.order_by('-fecha_emision')
    
    # Contadores
    total = facturas.count()
    aprobadas = facturas.filter(estado='aprobado').count()
    pendientes = facturas.filter(estado='pendiente').count()
    rechazadas = facturas.filter(estado='rechazado').count()
    
    # Segmentación
    descuento = 0
    segmento_nombre = "Sin segmentación"
    clientes_asociados = []
    cliente_operativo = None
    
    if request.user.is_authenticated:
        clientes_asociados, cliente_operativo = obtener_clientes_usuario(request.user, request)
        if (cliente_operativo and cliente_operativo.segmentacion and 
            cliente_operativo.segmentacion.estado == "activo"):
            descuento = float(cliente_operativo.segmentacion.descuento)
            segmento_nombre = cliente_operativo.segmentacion.nombre

    context = {
        "facturas": facturas,
        "total": total,
        "aprobadas": aprobadas,
        "pendientes": pendientes,
        "rechazadas": rechazadas,
        "segmento": segmento_nombre,
        "clientes_asociados": clientes_asociados,
        "cliente_operativo": cliente_operativo,
        'descuento': descuento,
    }

    return render(request, "facturacion/listarFacturas.html", context)


@csrf_exempt
@require_http_methods(["POST"])
def generar_factura_transaccion(request):
    """
    Genera una **factura electrónica** asociada a una transacción.

    Recibe un JSON con el `transaccion_id`, obtiene la información del cliente y
    usa el servicio `FacturaSeguraService` para emitir la factura ante SIFEN.

    **Parámetros:**

    - **request (HttpRequest):**  
      Solicitud HTTP POST con JSON `{ "transaccion_id": int }`.

    **Retorna:**

    - **JsonResponse:**  
      Resultado con éxito o error y datos de la factura generada.
    """
    try:
        data = json.loads(request.body)
        transaccion_id = data.get('transaccion_id')
        print(f"🧾 [GENERAR] Iniciando para transacción #{transaccion_id}", flush=True)
        
        transaccion = Transaccion.objects.get(id=transaccion_id)
        cliente = transaccion.cliente
        
        # Preparar datos
        transaccion_data = {
            'monto': float(transaccion.monto),
            'abreviacion_origen': transaccion.moneda_origen.abreviacion,  
            'abreviacion_destino': transaccion.moneda_destino.abreviacion,  
            'tasa_usada': float(transaccion.tasa_usada),
            'referencia': transaccion.id,
            'metodo_pago': transaccion.metodo_pago.nombre,
            'tipo': transaccion.tipo,
        }

        cliente_data = {
            'nombre_completo': cliente.nombre,
            'email': cliente.email,
            'cedula': cliente.cedula,
            'ruc': getattr(cliente, 'ruc', None),
            'dv_ruc': getattr(cliente, 'dv_ruc', "3"),
        }
        
        # ✅ Esta función YA hace todo (generar + consultar + email)
        service = FacturaSeguraService()
        resultado = service.generar_factura_cambio(transaccion_data, cliente_data, usuario=request.user)
        print(f"✅ [GENERAR] Resultado: {resultado}", flush=True)
        
        if resultado.get('success'):
            rango = RangoFacturacion.objects.get(id=resultado['rango_id'])
            numero_completo = resultado['numero_completo']
            partes = numero_completo.split('-')
            
            # Guardar factura
            factura = Factura.objects.create(
                establecimiento=partes[0],
                punto_expedicion=partes[1],
                numero_documento=partes[2],
                cdc=resultado['cdc'],
                cliente=cliente,
                transaccion=transaccion,
                rango_utilizado=rango,
                monto_total=transaccion.monto,
                moneda=transaccion.moneda_origen.nombre,
                tipo_cambio=transaccion.tasa_usada,
                operation_id=resultado['operation_id'],
                creado_por=request.user
            )
            
            resumen = factura_resumida(factura)
            factura.json_factura = resumen
            factura.save()
            
            return JsonResponse({
                'success': True,
                'factura_id': factura.id,
                'numero_factura': factura.numero_completo,
                'cdc': resultado['cdc'],
                'resumen': resumen,  
                'numeros_restantes': rango.numeros_disponibles,
                'message': 'Factura generada exitosamente'
            })
        else:
            return JsonResponse({
                'success': False,
                'error': resultado.get('error')
            }, status=400)
            
    except Transaccion.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Transacción no encontrada'
        }, status=404)
    except RangoFacturacion.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'No tienes un rango de facturación asignado'
        }, status=400)
    except Exception as e:
        import traceback
        print(f"❌ Error: {traceback.format_exc()}", flush=True)
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@require_http_methods(["GET"])
def consultar_estado_factura(request, factura_id):
    """
    Consulta el **estado en SIFEN** de una factura específica y actualiza su estado local.

    **Parámetros:**

    - **request (HttpRequest):**  
      Solicitud HTTP.

    - **factura_id (int):**  
      ID de la factura a consultar.

    **Retorna:**

    - **JsonResponse:**  
      Estado actualizado o mensaje de error.
    """
    try:
        factura = Factura.objects.get(id=factura_id, creado_por=request.user)
        
        service = FacturaSeguraService()
        estado = service.consultar_estado(
            factura.cdc,
            service.config['RUC_EMISOR']
        )
        
        if estado:
            # Actualizar factura
            factura.estado_sifen = estado.get('estado_sifen')
            factura.descripcion_sifen = estado.get('desc_sifen')
            
            if estado.get('estado_sifen') == 'Aprobado':
                factura.estado = 'aprobado'
                factura.fecha_aprobacion = timezone.now()
            elif estado.get('estado_sifen') == 'Rechazado':
                factura.estado = 'rechazado'
            
            factura.save()
            
            return JsonResponse({
                'success': True,
                'estado': factura.estado,
                'estado_sifen': factura.estado_sifen,
                'descripcion_sifen': factura.descripcion_sifen,
                'cdc': factura.cdc,
                'numero_factura': factura.numero_completo,
                'fecha_aprobacion': factura.fecha_aprobacion.isoformat() if factura.fecha_aprobacion else None
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'No se pudo consultar estado'
            }, status=400)
    
    except Factura.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Factura no encontrada'
        }, status=404)
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
        
@require_http_methods(["GET"])
def consultar_estado_factura_transaccion(request):
    """
    Consulta el estado SIFEN de la **factura vinculada a una transacción**.

    **Parámetros:**

    - **request (HttpRequest):**  
      Solicitud GET con `transaccion_id`.

    **Retorna:**

    - **JsonResponse:**  
      Estado de la factura o error.
    """
    try:
        transaccion_id = request.GET.get('transaccion_id')
        
        if not transaccion_id:
            return JsonResponse({
                "success": False,
                "error": "Se requiere transaccion_id"
            }, status=400)
        
        factura = Factura.objects.get(transaccion_id=transaccion_id)
        
        service = FacturaSeguraService()
        estado = service.consultar_estado(
            factura.cdc,
            service.config['RUC_EMISOR']
        )
        
        if estado:
            factura.estado_sifen = estado.get('estado_sifen')
            factura.descripcion_sifen = estado.get('desc_sifen')
            
            if estado.get('estado_sifen') == 'Aprobado':
                factura.estado = 'aprobado'
                factura.fecha_aprobacion = timezone.now()
            elif estado.get('estado_sifen') == 'Rechazado':
                factura.estado = 'rechazado'
            
            factura.save()
            
            return JsonResponse({
                'success': True,
                'estado': estado,
                'numero_factura': factura.numero_completo,
                'cdc': factura.cdc
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'No se pudo consultar el estado en SIFEN'
            }, status=400)
    
    except Factura.DoesNotExist:
        return JsonResponse({
            "success": False,
            "error": "Esta transacción no tiene factura generada"
        }, status=404)
    except Exception as e:
        return JsonResponse({
            "success": False,
            "error": str(e)
        }, status=500)


@require_http_methods(["GET"])
def descargar_factura(request):
    """
    Descarga el **KuDE (PDF)** de una factura emitida.

    **Parámetros:**

    - **request (HttpRequest):**  
      Solicitud GET con parámetros `cdc` y `transaccion_id`.

    **Retorna:**

    - **FileResponse:** Archivo PDF.  
    - **JsonResponse:** Mensaje de error en caso de fallo.
    """
    cdc = request.GET.get('cdc')
    transaccion_id = request.GET.get('transaccion_id')
    
    if not cdc or not transaccion_id:
        return JsonResponse({'success': False, 'error': 'Faltan parámetros'}, status=400)

    try:
        factura = Factura.objects.get(transaccion_id=transaccion_id, cdc=cdc, creado_por=request.user)
    except Factura.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Factura no encontrada'}, status=404)

    service = FacturaSeguraService()
    ruc_emisor = service.config['RUC_EMISOR']
    output_path = f'/tmp/kude_{cdc}.pdf'
    ok = service.descargar_kude(cdc, ruc_emisor, output_path)
    
    if not ok:
        return JsonResponse({'success': False, 'error': 'No se pudo descargar el KuDE'}, status=500)

    try:
        return FileResponse(open(output_path, 'rb'), as_attachment=True, filename=f'factura_{cdc}.pdf')
    except Exception:
        raise Http404("Archivo no encontrado")


def factura_resumida(factura):
    """
    Envía por **correo electrónico** el PDF (KuDE) de una factura generada.

    **Parámetros:**

    - **request (HttpRequest):**  
      Solicitud POST con JSON `{ "transaccion_id": int }`.

    **Retorna:**

    - **JsonResponse:**  
      Confirmación de envío o error.
    """
    ruc_cliente = factura.cliente.ruc or factura.cliente.cedula or "0"

    if ruc_cliente and '-' in ruc_cliente:
        numero_ruc_cliente, dv_cliente = ruc_cliente.split('-')
    else:
        numero_ruc_cliente = ruc_cliente
        dv_cliente = getattr(factura.cliente, "dv_ruc", "3")

    data = {
        "iTipEmi": "1",
        "iTiDE": "1",
        "dNumTim": "02595733",
        "dFeIniT": "2025-03-27",
        "dEst": factura.establecimiento,
        "dPunExp": factura.punto_expedicion,
        "dNumDoc": factura.numero_documento,
        "dFeEmiDE": factura.fecha_emision.strftime("%Y-%m-%dT%H:%M:%S"),
        "iTipTra": "2",
        "iTImp": "5",
        "cMoneOpe": "PYG",
        "dCondTiCam": "1",
        "dTiCam": str(factura.tipo_cambio),
        "dRucEm": "2595733",
        "dDVEmi": "3",
        "iTipCont": "1",
        "dNomEmi": "GLOBAL EXCHANGE S.A.",
        "dDirEmi": "AV. EUSEBIO AYALA KM 4.5",
        "dNumCas": "1543",
        "cDepEmi": "1",
        "dDesDepEmi": "CAPITAL",
        "cCiuEmi": "1",
        "dDesCiuEmi": "ASUNCION (DISTRITO)",
        "dTelEmi": "(0961)988439",
        "dEmailE": "facturacion@globalexchange.com.py",
        "gActEco": [
            {
                "cActEco": "74909",
                "dDesActEco": "Otras actividades profesionales, científicas y técnicas n.c.p."
            }
        ],
        "iNatRec": "1",
        "iTiOpe": "1",
        "cPaisRec": "PRY",
        "iTiContRec": "2",
        "dRucRec": numero_ruc_cliente,
        "dDVRec": dv_cliente,
        "dNomRec": factura.cliente.nombre,
        "dEmailRec": factura.cliente.email,
        "iIndPres": "1",
        "iCondOpe": "2",
        "gPaConEIni": [
            {
                "iTiPago": "1",
                "dMonTiPag": str(factura.monto_total),
                "cMoneTiPag": factura.moneda,
                "dTiCamTiPag": str(factura.tipo_cambio)
            }
        ],
        "gCamItem": [
            {
                "dCodInt": "SERV001",
                "dDesProSer": f"Servicio de cambio de divisas",
                "cUniMed": "77",
                "dCantProSer": "1",
                "dPUniProSer": str(factura.monto_total),
                "iAfecIVA": "1",
                "dTasaIVA": "10"
            }
        ],
        "CDC": factura.cdc or "0",
        "dCodSeg": "862814791",
        "dDVId": "0",
        "dSisFact": "1",
        "dInfAdic": f"Factura generada por el usuario {factura.creado_por.username}"
    }

    return data


def obtener_clientes_usuario(user, request):
    """
    Obtiene los **clientes asociados** a un usuario y el cliente operativo actual.

    Si existe un cliente operativo en sesión, se devuelve ese; de lo contrario, el primero.

    **Parámetros:**
    - **user (User):**  
      Usuario autenticado.
      
    - **request (HttpRequest):**  
      Solicitud actual.

    **Retorna:**

    - **tuple[list[Cliente], Cliente | None]:**  
      Lista de clientes asociados y el cliente operativo.
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

    return clientes_asociados, cliente_operativo


@login_required
def set_cliente_operativo(request):
    """Define el **cliente operativo** en sesión para el usuario autenticado."""
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