import requests
import json
from datetime import datetime

# ========== CONFIGURACIÓN ==========
API_URL = "https://apitest.facturasegura.com.py/misife00/v1/esi"
TOKEN = "eyJ2ZXIiOiI1IiwidWlkIjoiMWVlOTRiNmI3MDgyNDBhMDhiY2E5YTgwZWExODJhOTgiLCJzaWQiOjAsImV4cCI6MH0.aPfwVQ.tcnm1XzTnrCnhXyVaOKP9ljPxfo"  # 🔥 Reemplazar con tu token real

# Datos del emisor (tu empresa)
RUC_EMISOR = "2595733"
DV_EMISOR = "3"
TIMBRADO = "80002247"
FECHA_INICIO_TIMBRADO = "2023-12-27"

# ========== FUNCIONES ==========

def test_calcular_de():
    """
    Prueba 1: Calcular campos de una factura
    """
    print("\n" + "="*60)
    print("🧪 TEST 1: CALCULAR_DE")
    print("="*60)
    
    factura_resumida = {
        "iTipEmi": "1",
        "iTiDE": "1",
        "dNumTim": TIMBRADO,
        "dFeIniT": FECHA_INICIO_TIMBRADO,
        "dEst": "001",
        "dPunExp": "003",
        "dNumDoc": "0000001",
        "dFeEmiDE": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "iTipTra": "1",
        "iTImp": "1",
        "cMoneOpe": "PYG",
        "dCondTiCam": "1",
        "dTiCam": "1",
        
        # Emisor
        "dRucEm": RUC_EMISOR,
        "dDVEmi": DV_EMISOR,
        "iTipCont": "2",
        "dNomEmi": "EMPRESA TEST S.A.",
        "dDirEmi": "AV. TEST 123",
        "dNumCas": "123",
        "cDepEmi": "1",
        "dDesDepEmi": "CAPITAL",
        "cCiuEmi": "1",
        "dDesCiuEmi": "ASUNCION (DISTRITO)",
        "dTelEmi": "(021)123456",
        "dEmailE": "test@empresa.com",
        "gActEco": [
            {
                "cActEco": "66190",
                "dDesActEco": "Otras actividades auxiliares de servicios financieros"
            }
        ],
        
        # Receptor (cliente de prueba)
        "iNatRec": "1",
        "iTiOpe": "1",
        "cPaisRec": "PRY",
        "iTiContRec": "2",
        "dRucRec": "0",
        "dDVRec": "0",
        "iTipIDRec": "1",
        "dNumIDRec": "1234567",
        "dNomRec": "CLIENTE PRUEBA",
        "dEmailRec": "cliente@test.com",
        
        # Operación
        "iIndPres": "1",
        "iCondOpe": "1",
        "gPaConEIni": [
            {
                "iTiPago": "1",
                "dMonTiPag": "110000",
                "cMoneTiPag": "PYG",
                "dTiCamTiPag": "1"
            }
        ],
        
        # Items
        "gCamItem": [
            {
                "dCodInt": "TEST-001",
                "dDesProSer": "Servicio de cambio de prueba",
                "cUniMed": "77",
                "dCantProSer": "1",
                "dPUniProSer": "1000",
                "dDescItem": "0",
                "dDescGloItem": "0",
                "dAntPreUniIt": "0",
                "dAntGloPreUniIt": "0",
                "iAfecIVA": "1",
                "dPropIVA": "100",
                "dTasaIVA": "10"
            }
        ],
        
        "CDC": "0",
        "dCodSeg": "0",
        "dDVId": "0",
        "dSisFact": "1",
        "dInfAdic": "Factura de prueba - No válida"
    }
    
    payload = {
        "operation": "calcular_de",
        "params": {
            "DE": factura_resumida
        }
    }
    
    headers = {
        'Content-Type': 'application/json',
        'accept': 'application/json',
        'Authentication-Token': TOKEN
    }
    
    try:
        print("📤 Enviando solicitud a calcular_de...")
        response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
        
        print(f"📊 Status Code: {response.status_code}")
        result = response.json()
        print("result:", result)
        if result.get('code') == 0:
            print("✅ SUCCESS: Cálculo exitoso")
            print(f"📋 Operation ID: {result['operation_info']['id']}")
            
            # Mostrar algunos campos calculados
            de_calculado = result['results'][0]['DE']
            print(f"\n💰 TOTALES CALCULADOS:")
            print(f"   - Total Operación: {de_calculado.get('dTotOpe', 'N/A')}")
            print(f"   - IVA 10%: {de_calculado.get('dIVA10', 'N/A')}")
            print(f"   - Total IVA: {de_calculado.get('dTotIVA', 'N/A')}")
            print(f"   - Total General: {de_calculado.get('dTotGralOpe', 'N/A')}")
            
            return de_calculado
        else:
            print(f"❌ ERROR: {result.get('description')}")
            print(f"📄 Details: {json.dumps(result.get('results'), indent=2)}")
            return None
            
    except requests.exceptions.Timeout:
        print("⏱️ ERROR: Timeout (30s)")
        return None
    except requests.exceptions.RequestException as e:
        print(f"🔥 ERROR de conexión: {str(e)}")
        return None
    except Exception as e:
        print(f"💥 ERROR inesperado: {str(e)}")
        return None


def test_generar_de(factura_calculada):
    """
    Prueba 2: Generar documento electrónico
    ⚠️ ESTO GENERARÁ UNA FACTURA REAL - Usar solo en ambiente TEST
    """
    print("\n" + "="*60)
    print("🧪 TEST 2: GENERAR_DE")
    print("="*60)
    
    if not factura_calculada:
        print("❌ No hay factura calculada. Ejecuta primero test_calcular_de()")
        return None
    
    print("⚠️  ADVERTENCIA: Esto generará una factura real en SIFEN")
    confirmacion = input("¿Continuar? (escribe 'SI' para confirmar): ")
    
    if confirmacion != "SI":
        print("❌ Operación cancelada")
        return None
    
    payload = {
        "operation": "generar_de",
        "params": {
            "DE": factura_calculada
        }
    }
    
    headers = {
        'Content-Type': 'application/json',
        'accept': 'application/json',
        'Authentication-Token': TOKEN
    }
    
    try:
        print("📤 Enviando solicitud a generar_de...")
        response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
        
        print(f"📊 Status Code: {response.status_code}")
        print("responsetest_generar:", response)
        result = response.json()
        
        if result.get('code') == 0:
            cdc = result['results'][0]['CDC']
            print("✅ SUCCESS: Factura generada!")
            print(f"🔑 CDC: {cdc}")
            print(f"📋 Operation ID: {result['operation_info']['id']}")
            print("\n⏱️  Espera 1 minuto antes de consultar el estado")
            
            return cdc
        else:
            print(f"❌ ERROR: {result.get('description')}")
            print("resulttest_generar_de:", result)
            print(f"📄 Details: {json.dumps(result.get('results'), indent=2)}")
            return None
            
    except Exception as e:
        print(f"💥 ERROR: {str(e)}")
        return None


def test_consultar_estado(cdc):
    """
    Prueba 3: Consultar estado de una factura
    """
    print("\n" + "="*60)
    print("🧪 TEST 3: CONSULTAR ESTADO")
    print("="*60)
    
    if not cdc:
        print("❌ No hay CDC. Genera una factura primero.")
        return None
    
    payload = {
        "operation": "get_estado_sifen",
        "params": {
            "CDC": "01025957333001003000000122025102115087502146",
            "dRucEm": RUC_EMISOR
        }
    }
    
    headers = {
        'Content-Type': 'application/json',
        'accept': 'application/json',
        'Authentication-Token': TOKEN
    }
    
    try:
        print(f"📤 Consultando estado del CDC: {cdc}")
        response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
        
        print(f"📊 Status Code: {response.status_code}")
        
        result = response.json()
        
        if result.get('code') == 0:
            estado = result['results'][0]
            print("✅ SUCCESS: Estado obtenido")
            print(f"\n📊 ESTADO DE LA FACTURA:")
            print(f"   🔹 Estado SIFEN: {estado.get('estado_sifen', 'N/A')}")
            print(f"   🔹 Descripción: {estado.get('desc_sifen', 'N/A')}")
            print(f"   🔹 Error: {estado.get('error_sifen', 'N/A')}")
            print(f"   🔹 Fecha consulta: {estado.get('fch_sifen', 'N/A')}")
            
            # Estados de cancelación e inutilización
            if estado.get('estado_can'):
                print(f"   🔸 Cancelación: {estado.get('estado_can')}")
            if estado.get('estado_inu'):
                print(f"   🔸 Inutilización: {estado.get('estado_inu')}")
            
            return estado
        else:
            print(f"❌ ERROR: {result.get('description')}")
            print(f"📄 Details: {json.dumps(result.get('results'), indent=2)}")
            return None
            
    except Exception as e:
        print(f"💥 ERROR: {str(e)}")
        return None


def test_conexion():
    """
    Prueba 0: Verificar conectividad básica
    """
    print("\n" + "="*60)
    print("🧪 TEST 0: VERIFICAR CONEXIÓN")
    print("="*60)
    
    headers = {
        'Content-Type': 'application/json',
        'accept': 'application/json',
        'Authentication-Token': TOKEN
    }
    
    # Intentar consultar estado de un CDC inexistente (solo para probar conexión)
    payload = {
        "operation": "get_estado_sifen",
        "params": {
            "CDC": "01800022475001003000003022024041616519033170",
            "dRucEm": RUC_EMISOR
        }
    }
    
    try:
        print("📤 Probando conexión a API...")
        response = requests.post(API_URL, headers=headers, json=payload, timeout=10)
        
        print(f"✅ Conexión exitosa! Status: {response.status_code}")
        print("response:", response)

        if response.status_code == 200:
            print("response test_conexion:", response.json())
            print("response test_conexion:", response.json().get('description'))
            print("✅ Token válido (API respondió)")
            return True
        else:
            print(f"⚠️  Status inesperado: {response.status_code}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ ERROR: Timeout - El servidor no responde")
        
        return False
    except requests.exceptions.ConnectionError:
        print("❌ ERROR: No se puede conectar a la API")
        return False
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False


# ========== MENÚ PRINCIPAL ==========
def menu():
    """
    Menú interactivo para ejecutar pruebas
    """
    print("\n" + "🚀"*30)
    print("   SCRIPT DE PRUEBA - API FACTURA SEGURA")
    print("🚀"*30)
    
    if not TOKEN or TOKEN == "TU_TOKEN_AQUI":
        print("\n❌ ERROR: Debes configurar el TOKEN en el script")
        print("   Edita la variable TOKEN en la línea 7")
        return
    
    factura_calculada = None
    cdc_generado = None
    
    while True:
        print("\n" + "="*60)
        print("MENÚ DE PRUEBAS:")
        print("="*60)
        print("0. ✅ Test de conexión")
        print("1. 🧮 Calcular factura (calcular_de)")
        print("2. 📄 Generar factura (generar_de) ⚠️  GENERA FACTURA REAL")
        print("3. 🔍 Consultar estado (get_estado_sifen)")
        print("4. 🔄 Ejecutar todas las pruebas en secuencia")
        print("5. ❌ Salir")
        print("="*60)
        
        opcion = input("\nSelecciona una opción (0-5): ").strip()
        
        if opcion == "0":
            test_conexion()
            
        elif opcion == "1":
            factura_calculada = test_calcular_de()
            
        elif opcion == "2":
            if not factura_calculada:
                print("\n⚠️  Primero debes calcular una factura (opción 1)")
            else:
                cdc_generado = test_generar_de(factura_calculada)
                
        elif opcion == "3":
            if not cdc_generado:
                cdc_manual = input("Ingresa el CDC a consultar: ").strip()
                if cdc_manual:
                    test_consultar_estado(cdc_manual)
                else:
                    print("❌ CDC vacío")
            else:
                test_consultar_estado(cdc_generado)
                
        elif opcion == "4":
            print("\n🔄 EJECUTANDO TODAS LAS PRUEBAS...")
            
            # Test 0: Conexión
            if not test_conexion():
                print("\n❌ Abortando: No hay conexión")
                continue
            
            # Test 1: Calcular
            factura_calculada = test_calcular_de()
            if not factura_calculada:
                print("\n❌ Abortando: Error en cálculo")
                continue
            
            # Test 2: Generar
            print("\n⚠️  La siguiente prueba generará una factura REAL")
            confirmacion = input("¿Continuar con generar_de? (SI/NO): ")
            if confirmacion != "SI":
                print("❌ Prueba de generación omitida")
                continue
                
            cdc_generado = test_generar_de(factura_calculada)
            if not cdc_generado:
                print("\n❌ Error al generar factura")
                continue
            
            # Esperar 1 minuto
            print("\n⏱️  Esperando 60 segundos antes de consultar estado...")
            import time
            for i in range(60, 0, -10):
                print(f"   {i} segundos restantes...")
                time.sleep(10)
            
            # Test 3: Consultar
            test_consultar_estado(cdc_generado)
            
            print("\n✅ TODAS LAS PRUEBAS COMPLETADAS")
            
        elif opcion == "5":
            print("\n👋 ¡Hasta luego!")
            break
            
        else:
            print("❌ Opción inválida")
        
        input("\n⏸️  Presiona ENTER para continuar...")


if __name__ == "__main__":
    menu()