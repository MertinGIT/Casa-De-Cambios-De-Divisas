from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.http import FileResponse, Http404

import json
from .services import FacturaSeguraService
from .models import Factura, RangoFacturacion
from operaciones.models import Transaccion
from clientes.models import Cliente

@csrf_exempt
@require_http_methods(["POST"])
def generar_factura_transaccion(request):
    """
    Genera factura para una transacción
    """
    try:
        data = json.loads(request.body)
        transaccion_id = data.get('transaccion_id')
        print("transaccion_id:", transaccion_id, flush=True)
        
        # Obtener transacción
        transaccion = Transaccion.objects.get(id=transaccion_id)
        print("transaccion:", transaccion, flush=True)
        cliente = transaccion.cliente
        
        # Preparar datos
        transaccion_data = {
            'monto': float(transaccion.monto),
            'moneda': transaccion.moneda_origen.abreviacion,  
            'tipo_cambio': float(transaccion.tasa_usada),
            'referencia': transaccion.id,
            'metodo_pago_id': transaccion.metodo_pago.nombre,
            'tipo': transaccion.tipo,
        }

        print("transaccion_data:", transaccion_data, flush=True)

        cliente_data = {
            'nombre_completo': cliente.nombre,
            'email': cliente.email,
            'cedula': cliente.cedula,
            'ruc': getattr(cliente, 'ruc', None),
            'dv_ruc': getattr(cliente, 'dv_ruc', "3"),
        }

        print("cliente_data:", cliente_data, flush=True)
        
        # Generar factura
        service = FacturaSeguraService()
        resultado = service.generar_factura_cambio(transaccion_data, cliente_data, usuario=request.user)
        print("resultado factura views facturacion:", resultado, flush=True)
        
        if resultado.get('success'):
            rango = RangoFacturacion.objects.get(id=resultado['rango_id'])
            
            # ✅ CORRECCIÓN: Extraer el número del resultado
            numero_completo = resultado['numero_completo']  # "001-003-0000001"
            partes = numero_completo.split('-')
            
            # Guardar factura - el método save() generará automáticamente el campo 'numero'
            factura = Factura.objects.create(
                establecimiento=partes[0],  # "001"
                punto_expedicion=partes[1],  # "003"
                numero_documento=partes[2],  # "0000001"
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
            print("Resumen de factura:", resumen, flush=True)
            
            return JsonResponse({
                'success': True,
                'factura_id': factura.id,
                'numero_factura': factura.numero_completo,  # Usará el property
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
        print(f"Error completo: {traceback.format_exc()}", flush=True)
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_http_methods(["GET"])
def consultar_estado_factura(request):
    transaccion_id = request.GET.get("transaccion_id")
    
    if not transaccion_id:
        return JsonResponse({
            "success": False,
            "error": "Se requiere transaccion_id"
        }, status=400)
    
    try:
        # Buscar factura por la transacción
        factura = Factura.objects.get(transaccion__id=transaccion_id)
        
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
                'estado': estado,
                'cdc': factura.cdc,
                'numero_factura': factura.numero_completo
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


def consultar_estado_factura_transaccion(request):
    """
    Consulta el estado de la factura asociada a una transacción en SIFEN.
    """
    if request.method != "GET":
        return JsonResponse({"success": False, "error": "Método no permitido"}, status=405)
    
    try:
        transaccion_id = request.GET.get('transaccion_id')
        
        if not transaccion_id:
            return JsonResponse({
                "success": False,
                "error": "Se requiere transaccion_id"
            }, status=400)
        
        # Buscar la factura asociada a la transacción
        factura = Factura.objects.get(transaccion_id=transaccion_id)
        
        # Consultar estado en SIFEN
        service = FacturaSeguraService()
        estado = service.consultar_estado(
            factura.cdc,
            service.config['RUC_EMISOR']
        )
        
        if estado:
            # Actualizar estado de la factura
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


def factura_resumida(factura):
    """
    Devuelve un diccionario con los datos resumidos de la factura.
    """
    from datetime import datetime
    
    # Usar RUC si existe, sino cédula
    ruc_cliente = factura.cliente.ruc or factura.cliente.cedula or "0"

    # Separar dígito verificador si hay guion
    if ruc_cliente and '-' in ruc_cliente:
        numero_ruc_cliente, dv_cliente = ruc_cliente.split('-')
    else:
        numero_ruc_cliente = ruc_cliente
        dv_cliente = getattr(factura.cliente, "dv_ruc", "3")

    data = {
        "iTipEmi": "1",
        "iTiDE": "1",
        "dNumTim": getattr(factura, "timbrado", "00000000"),
        "dFeIniT": getattr(factura, "fecha_emision", datetime.now()).strftime("%Y-%m-%dT%H:%M:%S"),
        "dEst": factura.establecimiento,
        "dPunExp": factura.punto_expedicion,
        "dNumDoc": factura.numero_documento,
        "dFeEmiDE": factura.fecha_emision.strftime("%Y-%m-%dT%H:%M:%S"),
        "iTipTra": "1",
        "iTImp": "1",
        "cMoneOpe": factura.moneda,
        "dCondTiCam": "1",
        "dTiCam": str(factura.tipo_cambio),

        # Emisor
        "dRucEm": "80012345",
        "dDVEmi": "3",
        "iTipCont": "2",
        "dNomEmi": "EMPRESA TEST S.A.",
        "dDirEmi": "AV. TEST 123",
        "dNumCas": "123",
        "cDepEmi": "1",
        "dDesDepEmi": "CAPITAL",
        "cCiuEmi": "1",
        "dDesCiuEmi": "ASUNCION",
        "dTelEmi": "(021)123456",
        "dEmailE": "test@empresa.com",
        "gActEco": [
            {
                "cActEco": "66190",
                "dDesActEco": "Otras actividades auxiliares de servicios financieros"
            }
        ],

        # Receptor
        "iNatRec": "1",
        "iTiOpe": "1",
        "cPaisRec": "PRY",
        "iTiContRec": "2",
        "dRucRec": numero_ruc_cliente,
        "dDVRec": dv_cliente,
        "iTipIDRec": "1",
        "dNumIDRec": factura.cliente.cedula,
        "dNomRec": factura.cliente.nombre,
        "dEmailRec": factura.cliente.email,

        # Operación
        "iIndPres": "1",
        "iCondOpe": "1",
        "gPaConEIni": [
            {
                "iTiPago": "1",
                "dMonTiPag": str(factura.monto_total),
                "cMoneTiPag": factura.moneda,
                "dTiCamTiPag": str(factura.tipo_cambio)
            }
        ],

        # Item
        "gCamItem": [
            {
                "dCodInt": "SERV001",
                "dDesProSer": "Servicio de cambio de divisas",
                "cUniMed": "77",
                "dCantProSer": "1",
                "dPUniProSer": str(factura.monto_total),
                "iAfecIVA": "1",
                "dTasaIVA": "10"
            }
        ],

        # Datos finales
        "CDC": factura.cdc or "0",
        "dCodSeg": "0",
        "dDVId": "0",
        "dSisFact": "1",
        "dInfAdic": f"Factura generada por el usuario {factura.creado_por.username}"
    }

    return data

@require_http_methods(["GET"])
def descargar_factura(request):
    """
    Descarga el KuDE (PDF) de la factura usando el CDC y el RUC emisor.
    Espera los parámetros GET: cdc y transaccion_id
    """
    cdc = request.GET.get('cdc')
    transaccion_id = request.GET.get('transaccion_id')
    if not cdc or not transaccion_id:
        return JsonResponse({'success': False, 'error': 'Faltan parámetros'}, status=400)

    # Busca la factura asociada a la transacción
    try:
        factura = Factura.objects.get(transaccion_id=transaccion_id, cdc=cdc)
    except Factura.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Factura no encontrada'}, status=404)

    # Llama al service para descargar el PDF
    service = FacturaSeguraService()
    ruc_emisor = service.config['RUC_EMISOR']
    output_path = f'/tmp/kude_{cdc}.pdf'
    ok = service.descargar_kude(cdc, ruc_emisor, output_path)
    if not ok:
        return JsonResponse({'success': False, 'error': 'No se pudo descargar el KuDE'}, status=500)

    # Devuelve el archivo PDF
    try:
        return FileResponse(open(output_path, 'rb'), as_attachment=True, filename=f'factura_{cdc}.pdf')
    except Exception:
        raise Http404("Archivo no encontrado")