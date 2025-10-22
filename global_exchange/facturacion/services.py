from django.forms import ValidationError
import requests
import json
from datetime import datetime
from django.conf import settings
from django.db import transaction

from facturacion.models import RangoFacturacion
class FacturaSeguraService:
    
    def __init__(self):
        self.config = settings.FACTURA_SEGURA
        self.api_url = self.config['API_URL']
        self.token = self.config['TOKEN']
        self.headers = {
            'Content-Type': 'application/json',
            'accept': 'application/json',
            'Authentication-Token': self.token
        }
    
    def generar_factura_cambio(self, transaccion_data, cliente_data, usuario=None):
        """
        Genera factura electrónica usando el rango del usuario
        """
        # Obtener rango activo del usuario
        rango = self._obtener_rango_usuario(usuario)
        
        if not rango:
            return {
                'success': False,
                'error': 'No tienes un rango de facturación asignado'
            }
        
        # Verificar si hay números disponibles
        if rango.numeros_disponibles <= 0:
            return {
                'success': False,
                'error': f'Rango agotado. Último número: {rango.numero_fin}'
            }
        
        # Alerta si quedan pocos números
        if rango.numeros_disponibles <= 10:
            print(f"⚠️  ADVERTENCIA: Solo quedan {rango.numeros_disponibles} números disponibles")
        
        try:
            with transaction.atomic():
                # Obtener siguiente número (incrementa automáticamente)
                numero_doc = rango.obtener_siguiente_numero()
                
                # Construir JSON con el número asignado
                factura_json = self._construir_json_factura(
                    transaccion_data, 
                    cliente_data,
                    establecimiento=rango.establecimiento,
                    punto_expedicion=rango.punto_expedicion,
                    numero_documento=numero_doc
                )
                
                # Calcular y generar
                factura_calculada = self.calcular_de(factura_json)
                
                if not factura_calculada:
                    # Si falla, revertir el incremento
                    rango.numero_actual -= 1
                    rango.save()
                    return {'error': 'Error al calcular factura'}
                
                resultado = self.generar_de(factura_calculada)
                
                if resultado.get('success'):
                    resultado['numero_completo'] = f"{rango.establecimiento}-{rango.punto_expedicion}-{numero_doc}"
                    resultado['rango_id'] = rango.id
                else:
                    # Si falla, revertir el incremento
                    rango.numero_actual -= 1
                    rango.save()
                
                return resultado
                
        except ValidationError as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _obtener_rango_usuario(self, usuario):
        """
        Obtiene el rango activo del usuario o crea uno por defecto si no existe
        """
        if not usuario:
            return None

        rango = RangoFacturacion.objects.filter(
            usuario=usuario,
            activo=True
        ).order_by('numero_actual').first()

        # Si no tiene rango, se crea uno nuevo por defecto
        if not rango:
            rango = RangoFacturacion.objects.create(
                establecimiento='001',
                punto_expedicion='003',
                numero_inicio=1,
                numero_fin=50,
                numero_actual=1,
                usuario=usuario,
                activo=True
            )
        
        return rango


    def _construir_json_factura(self, transaccion, cliente, establecimiento, punto_expedicion, numero_documento):
        """
        Construye el JSON resumido de la factura
        """
        # Determinar tipo de cambio
        #tipo_cambio = transaccion.get('tipo_cambio', 7350)
        #monto = float(transaccion.get('monto', 0))
        

        # Calcular comisión (ejemplo: 2%)
        comision = transaccion['monto'] * 0.02
        print("transaccion _construir_json_factura:", transaccion, flush=True)
        factura = {
            "iTipEmi": "1",
            "iTiDE": "1",  # Factura electrónica
            "dNumTim": self.config['TIMBRADO'],
            "dFeIniT": self.config['FECHA_INICIO_TIMBRADO'],
            "dEst": establecimiento,  # ✅ Usa el del rango
            "dPunExp": punto_expedicion,  # ✅ Usa el del rango
            "dNumDoc": numero_documento,  # ✅ Usa el del rango
            "dFeEmiDE": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            "iTipTra": "1",
            "iTImp": "1",
            "cMoneOpe": transaccion['moneda'],
            "dCondTiCam": "1",
            "dTiCam": str(transaccion['tipo_cambio']) if transaccion['moneda'] != 'PYG' else "1",
            
            # Datos del EMISOR (tu empresa)
            "dRucEm": self.config['RUC_EMISOR'],
            "dDVEmi": self.config['DV_EMISOR'],
            "iTipCont": "2",
            "dNomEmi": "TU EMPRESA S.A.",
            "dDirEmi": "Tu Dirección",
            "dNumCas": "123",
            "cDepEmi": "1",
            "dDesDepEmi": "CAPITAL",
            "cCiuEmi": "1",
            "dDesCiuEmi": "ASUNCION (DISTRITO)",
            "dTelEmi": "(021)123456",
            "dEmailE": "facturacion@tuempresa.com",
            "gActEco": [
                {
                    "cActEco": "66190",
                    "dDesActEco": "Otras actividades auxiliares de servicios financieros"
                }
            ],
            
            # Datos del RECEPTOR (cliente)
            "iNatRec": "1",
            "iTiOpe": "1",
            "cPaisRec": "PRY",
            "iTiContRec": self._determinar_tipo_contribuyente(cliente),
            "dRucRec": cliente.get('cedula', '0'),
            "dDVRec": cliente.get('dv_ruc', '3'),
            "iTipIDRec": "1" if not cliente.get('cedula') else "0",
            "dNumIDRec": cliente.get('cedula', '0'),
            "dNomRec": cliente.get('nombre_completo', 'CLIENTE'),
            "dEmailRec": cliente.get('email', 'cliente@email.com'),
            
            # Condición de operación
            "iIndPres": "1",
            "iCondOpe": "1",  # Contado
            
            # Forma de pago
            "gPaConEIni": [
                {
                    "iTiPago": self._mapear_metodo_pago(transaccion['metodo_pago_id']),
                    "dMonTiPag": str(int(transaccion['monto'] + comision)),
                    "cMoneTiPag": transaccion['moneda'],
                    "dTiCamTiPag": "1"
                }
            ],
            
            # Items de la factura
            "gCamItem": [
                {
                    "dCodInt": "CAMBIO-001",
                    "dDesProSer": f"Servicio de cambio {transaccion.get('motivo', '')}",
                    "cUniMed": "77",
                    "dCantProSer": "1",
                    "dPUniProSer": str(transaccion['monto']),
                    "dDescItem": "0",
                    "dDescGloItem": "0",
                    "dAntPreUniIt": "0",
                    "dAntGloPreUniIt": "0",
                    "iAfecIVA": "1",  # Gravado IVA
                    "dPropIVA": "100",
                    "dTasaIVA": "10"
                },
                {
                    "dCodInt": "COMISION-001",
                    "dDesProSer": "Comisión por servicio de cambio",
                    "cUniMed": "77",
                    "dCantProSer": "1",
                    "dPUniProSer": str(int(comision)),
                    "dDescItem": "0",
                    "dDescGloItem": "0",
                    "dAntPreUniIt": "0",
                    "dAntGloPreUniIt": "0",
                    "iAfecIVA": "1",
                    "dPropIVA": "100",
                    "dTasaIVA": "10"
                }
            ],
            
            # ✅ CAMPOS CRÍTICOS - Deben ser "0" para que Factura Segura los genere
            "CDC": "0",  # ✅ CAMBIO CRÍTICO
            "dCodSeg": "0",
            "dDVId": "0",
            "dSisFact": "1",
            "dInfAdic": f"Transacción: {transaccion.get('referencia', '')}"
        }
        return factura
    
    
    
    def calcular_de(self, factura_json):
        """
        Calcula campos de la factura usando la API
        """
        payload = {
            "operation": "calcular_de",
            "params": {
                "DE": factura_json
            }
        }
        
        try:
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            result = response.json()
            
            if result.get('code') == 0:
                return result['results'][0]['DE']
            else:
                print(f"Error calcular_de: {result.get('description')}", flush=True)
                return None
                
        except Exception as e:
            print(f"Error en calcular_de: {str(e)}", flush=True)
            return None
    
    def generar_de(self, factura_completa):
        """
        Genera el documento electrónico
        """
        payload = {
            "operation": "generar_de",
            "params": {
                "DE": factura_completa
            }
        }
        
        try:
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            result = response.json()
            
            if result.get('code') == 0:
                cdc = result['results'][0]['CDC']
                return {
                    'success': True,
                    'cdc': cdc,
                    'operation_id': result['operation_info']['id']
                }
            else:
                return {
                    'success': False,
                    'error': result.get('description'),
                    'details': result.get('results')
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def consultar_estado(self, cdc, ruc_emisor):
        """
        Consulta el estado del documento en SIFEN
        """
        payload = {
            "operation": "get_estado_sifen",
            "params": {
                "CDC": cdc,
                "dRucEm": ruc_emisor
            }
        }
        
        try:
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            result = response.json()
            
            if result.get('code') == 0:
                return result['results'][0]
            else:
                return None
                
        except Exception as e:
            print(f"Error consultar estado: {str(e)}")
            return None
    
    def descargar_kude(self, cdc, ruc_emisor, output_path):
        """
        Descarga el PDF (KuDE)
        """
        url = f"{self.api_url}/dwn_kude/{ruc_emisor}/{cdc}"
        
        try:
            response = requests.get(
                url,
                headers={'Authentication-Token': self.token},
                timeout=30
            )
            response.raise_for_status()
            
            with open(output_path, 'wb') as f:
                f.write(response.content)
            
            return True
        except Exception as e:
            print(f"Error descargar KuDE: {str(e)}")
            return False
    
    def _generar_numero_factura(self):
        """
        Genera el siguiente número de factura
        Debes implementar tu lógica de numeración secuencial
        """
        # IMPORTANTE: Implementar lógica para obtener último número
        from facturacion.models import Factura
        ultimo = Factura.objects.order_by('-numero').first()
        if ultimo:
            return str(int(ultimo.numero) + 1).zfill(7)
        return "0000001"
    
    def _determinar_tipo_contribuyente(self, cliente):
        """
        Determina tipo de contribuyente
        1: Contribuyente, 2: No contribuyente
        """
        return "1" if cliente.get('ruc') else "2"
    
    def _mapear_metodo_pago(self, metodo_id):
        """
        Mapea tu método de pago a los códigos SIFEN
        1: Efectivo, 2: Cheque, 3: Tarjeta, 4: Tarjeta débito, 5: Transferencia
        """
        mapeo = {
            1: "1",  # Efectivo
            2: "5",  # Transferencia
            3: "3",  # Tarjeta
        }
        return mapeo.get(metodo_id, "1")