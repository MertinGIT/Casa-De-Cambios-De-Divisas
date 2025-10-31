from django.forms import ValidationError
import requests
import json
from datetime import datetime
from django.conf import settings
from django.db import transaction

from facturacion.models import RangoFacturacion
class FacturaSeguraService:
    """
    Servicio de integración con la **API de FacturaSegura**.

    Esta clase centraliza toda la lógica de conexión y comunicación con el sistema
    de facturación electrónica, incluyendo generación, cálculo, consulta de estado
    y descarga del **KuDE (PDF)**.

    Se encarga de:
    - Gestionar los **rangos de facturación** por usuario.
    - Construir y enviar los **documentos electrónicos (DE)** al servicio externo.
    - Manejar las respuestas y errores del API.
    """
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
        Genera una **factura electrónica** asociada a una transacción de cambio de divisas.

        Este método se encarga de:
        - Obtener o crear un rango de facturación activo.
        - Asignar el siguiente número de factura disponible.
        - Construir la estructura DE (documento electrónico).
        - Enviar los datos a la API de FacturaSegura para cálculo y generación.

        **Parámetros:**

        - **transaccion_data (dict):**  
          Información de la transacción (monto, tipo de cambio, método de pago, etc.).

        - **cliente_data (dict):**  
          Datos del cliente (nombre, cédula, RUC, correo electrónico, etc.).

        - **usuario (User | None):**  
          Usuario autenticado que emite la factura.

        **Retorna:**

        - **dict:**  
          Resultado de la operación con claves:
          - `success (bool)`
          - `cdc (str, opcional)`
          - `operation_id (int, opcional)`
          - `numero_completo (str, opcional)`
          - `rango_id (int, opcional)`
          - `error (str, opcional)`
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
        Obtiene el **rango de facturación activo** del usuario.

        Si no existe uno, se crea automáticamente un rango por defecto.

        **Parámetros:**
        - **usuario (User):** Usuario autenticado.

        **Retorna:**
        - **RangoFacturacion | None:** Rango activo o `None` si no aplica.
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
        Construye el **JSON del Documento Electrónico (DE)** en formato oficial.

        **Parámetros:**
        - **transaccion (dict):** Datos de la operación (monto, moneda, tipo_cambio...).
        - **cliente (dict):** Datos del cliente.
        - **establecimiento (str):** Código de establecimiento.
        - **punto_expedicion (str):** Punto de expedición.
        - **numero_documento (int):** Número fiscal asignado.

        **Retorna:**
        - **dict:** Estructura lista para enviar al endpoint de cálculo o generación.
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
            "dNumTim": "02595733",
            "dFeIniT": "2025-03-27",
            "dEst": establecimiento, 
            "dPunExp": punto_expedicion,
            "dNumDoc": numero_documento,
            "dFeEmiDE": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            "iTipTra": "2",
            "iTImp": "5",
            "cMoneOpe": "PYG",
            "dCondTiCam": "1",
            "dTiCam": str(transaccion['tasa_usada']) if transaccion['abreviacion_origen'] != 'PYG' else "1",
            
            # Datos del EMISOR (tu empresa)
            "dRucEm": self.config['RUC_EMISOR'],
            "dDVEmi": self.config['DV_EMISOR'],
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
            
            # Datos del RECEPTOR (cliente)
            "iNatRec": "1",
            "iTiOpe": "1",
            "cPaisRec": "PRY",
            "iTiContRec": "2",
            "dRucRec": "80026216",
            "dDVRec": "6",
            "iTipIDRec": "1",
            "dNumIDRec": cliente.get('cedula', '0'),
            "dNomRec": cliente.get('nombre_completo', 'CLIENTE'),
            "dEmailRec": cliente.get('email', 'leandro.f3418@fpuna.edu.py'),
            
            # Condición de operación
            "iIndPres": "1",
            "iCondOpe": "1",  # Contado
            
            # Forma de pago
            "gPaConEIni": [
                {
                    "iTiPago": self._mapear_metodo_pago(transaccion['metodo_pago']),
                    "dMonTiPag": str(int(transaccion['monto'] + comision)),
                    "cMoneTiPag": transaccion['abreviacion_origen'],
                    "dTiCamTiPag": "1"
                }
            ],
            
            # Items de la factura
            "gCamItem": [
                {
                    "dCodInt": "CAMBIO-001",
                    "dDesProSer": f"Servicio de {transaccion['tipo']} de divisas - "
                    f"({transaccion['abreviacion_origen']}) → "
                    f"({transaccion['abreviacion_destino'] }) | "
                    f"Tasa: {transaccion['tasa_usada']}",
                    "dInfItem": (
                        f"Tasa utilizada: {transaccion['tasa_usada']} "
                        f"{transaccion['abreviacion_origen']}/{transaccion['abreviacion_destino']}"
                    ),
                    "cUniMed": "77",
                    "dCantProSer": "1",
                    "dPUniProSer": str(transaccion['monto']),
                    "dDescItem": "0",
                    "dDescGloItem": "0",
                    "dAntPreUniIt": "0",
                    "dAntGloPreUniIt": "0",
                    "iAfecIVA": "3",  # Gravado IVA
                    "dPropIVA": "0",
                    "dTasaIVA": "0"
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
                    "iAfecIVA": "3",
                    "dPropIVA": "0",
                    "dTasaIVA": "0"
                }
            ],
            
            # ✅ CAMPOS CRÍTICOS - Deben ser "0" para que Factura Segura los genere
            "CDC": "0",  # ✅ CAMBIO CRÍTICO
            "dCodSeg": "862814791",
            "dDVId": "0",
            "dSisFact": "1",
            #"dInfAdic": f"Transacción: {transaccion.get('referencia', '')}"
        }
        return factura
    
    
    
    def calcular_de(self, factura_json):
        """
        Envía una factura para que la **API FacturaSegura** calcule los campos automáticos del DE.

        **Parámetros:**
        - **factura_json (dict):** Documento electrónico base.

        **Retorna:**
        - **dict | None:** Documento electrónico completo o `None` si hubo error.
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
        Envía una factura **ya calculada** para su **generación oficial** en SIFEN.

        **Parámetros:**
        - **factura_completa (dict):** Documento electrónico final.

        **Retorna:**
        - **dict:** Resultado con `success`, `cdc`, `operation_id` o mensaje de error.
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
        Consulta el **estado actual en SIFEN** de una factura emitida.

        **Parámetros:**
        - **cdc (str):** Código de control del comprobante.
        - **ruc_emisor (str):** RUC del emisor.

        **Retorna:**
        - **dict | None:** Resultado con datos del estado o `None` si falla.
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
        Descarga el archivo **KuDE (PDF)** correspondiente a una factura electrónica.

        **Parámetros:**
        - **cdc (str):** Código de control CDC.
        - **ruc_emisor (str):** RUC del emisor.
        - **output_path (str):** Ruta destino donde guardar el archivo PDF.

        **Retorna:**
        - **bool:** `True` si la descarga fue exitosa, `False` en caso de error.
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
        """Obtiene el número de factura secuencial a partir del último registro."""

        # IMPORTANTE: Implementar lógica para obtener último número
        from facturacion.models import Factura
        ultimo = Factura.objects.order_by('-numero').first()
        if ultimo:
            return str(int(ultimo.numero) + 1).zfill(7)
        return "0000001"
    
    def _determinar_tipo_contribuyente(self, cliente):
        """Retorna '1' si el cliente tiene RUC (contribuyente), '2' si no."""
        return "1" if cliente.get('ruc') else "2"
    
    def _mapear_metodo_pago(self, metodo_id):
        """
        Convierte el ID interno del método de pago al código SIFEN correspondiente.

        **Parámetros:**
        - **metodo_id (int):** ID del método de pago.

        **Retorna:**
        - **str:** Código SIFEN (`1`=Efectivo, `3`=Tarjeta, `5`=Transferencia).
        """
        mapeo = {
            1: "1",  # Efectivo
            2: "5",  # Transferencia
            3: "3",  # Tarjeta
        }
        return mapeo.get(metodo_id, "1")