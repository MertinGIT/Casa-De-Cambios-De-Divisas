# poblar_db.py
import os
import django
import random
from datetime import timedelta
from django.utils import timezone
from decimal import Decimal

# Configuración Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "banco_simulado.settings")
django.setup()

from transaccion.models import Cliente, Transaccion, Cuenta, Moneda, Entidad, TasaCambio, Comision

# Crear monedas
def crear_monedas():
    monedas_data = [
        {"codigo": "PYG", "nombre": "Guaraní Paraguayo"},
        {"codigo": "USD", "nombre": "Dólar Estadounidense"},
        {"codigo": "EUR", "nombre": "Euro"},
        {"codigo": "BRL", "nombre": "Real Brasileño"},
        {"codigo": "ARS", "nombre": "Peso Argentino"},
    ]
    
    monedas = {}
    for data in monedas_data:
        moneda, created = Moneda.objects.get_or_create(codigo=data["codigo"], defaults=data)
        monedas[data["codigo"]] = moneda
        if created:
            print(f"✅ Moneda creada: {moneda.codigo}")
    
    return monedas

# Crear entidades bancarias
def crear_entidades():
    entidades_data = [
        "Banco Central del Paraguay",
        "Banco Itaú",
        "Banco BBVA",
        "Banco Regional",
        "Banco Continental",
        "Sudameris Bank",
    ]
    
    entidades = {}
    for nombre in entidades_data:
        entidad, created = Entidad.objects.get_or_create(nombre=nombre)
        entidades[nombre] = entidad
        if created:
            print(f"✅ Entidad creada: {entidad.nombre}")
    
    return entidades

# Crear clientes
def crear_clientes():
    clientes_data = [
        {
            "email": "juan.perez@example.com", 
            "nombre": "Juan Pérez", 
            "documento": "12345678",
            "telefono": "+595981123456"
        },
        {
            "email": "maria.gomez@example.com", 
            "nombre": "María Gómez", 
            "documento": "87654321",
            "telefono": "+595981234567"
        },
        {
            "email": "carlos.lopez@example.com", 
            "nombre": "Carlos López", 
            "documento": "11223344",
            "telefono": "+595981345678"
        },
        {
            "email": "ana.rodriguez@example.com", 
            "nombre": "Ana Rodríguez", 
            "documento": "44332211",
            "telefono": "+595981456789"
        },
        {
            "email": "luis.martinez@example.com", 
            "nombre": "Luis Martínez", 
            "documento": "55667788",
            "telefono": "+595981567890"
        },
    ]

    clientes = []
    for data in clientes_data:
        cliente, created = Cliente.objects.get_or_create(email=data["email"], defaults=data)
        clientes.append(cliente)
        if created:
            print(f"✅ Cliente creado: {cliente.nombre}")
    
    return clientes

# Crear cuentas para los clientes
def crear_cuentas(clientes, monedas, entidades):
    cuentas_data = [
        {"cliente_idx": 0, "nro_cuenta": "001-12345678", "moneda": "PYG", "entidad": "Banco Central del Paraguay", "saldo": 1500000.50, "tipo": "ahorro"},
        {"cliente_idx": 0, "nro_cuenta": "001-12345679", "moneda": "USD", "entidad": "Banco Central del Paraguay", "saldo": 2500.00, "tipo": "corriente"},
        
        {"cliente_idx": 1, "nro_cuenta": "002-87654321", "moneda": "USD", "entidad": "Banco Itaú", "saldo": 3200.00, "tipo": "ahorro"},
        {"cliente_idx": 1, "nro_cuenta": "002-87654322", "moneda": "PYG", "entidad": "Banco Itaú", "saldo": 850000.75, "tipo": "corriente"},
        
        {"cliente_idx": 2, "nro_cuenta": "003-11223344", "moneda": "EUR", "entidad": "Banco BBVA", "saldo": 1750.75, "tipo": "ahorro"},
        {"cliente_idx": 2, "nro_cuenta": "003-11223345", "moneda": "USD", "entidad": "Banco BBVA", "saldo": 1200.00, "tipo": "inversion"},
        
        {"cliente_idx": 3, "nro_cuenta": "004-44332211", "moneda": "PYG", "entidad": "Banco Regional", "saldo": 2200000.00, "tipo": "ahorro"},
        {"cliente_idx": 3, "nro_cuenta": "004-44332212", "moneda": "BRL", "entidad": "Banco Regional", "saldo": 5500.50, "tipo": "corriente"},
        
        {"cliente_idx": 4, "nro_cuenta": "005-55667788", "moneda": "ARS", "entidad": "Sudameris Bank", "saldo": 180000.25, "tipo": "ahorro"},
        {"cliente_idx": 4, "nro_cuenta": "005-55667789", "moneda": "USD", "entidad": "Sudameris Bank", "saldo": 950.00, "tipo": "corriente"},
    ]

    cuentas = []
    for data in cuentas_data:
        cliente = clientes[data["cliente_idx"]]
        moneda = monedas[data["moneda"]]
        entidad = entidades[data["entidad"]]
        
        cuenta, created = Cuenta.objects.get_or_create(
            nro_cuenta=data["nro_cuenta"],
            defaults={
                "cliente": cliente,
                "moneda": moneda,
                "entidad": entidad,
                "saldo": Decimal(str(data["saldo"])),
                "tipo_cuenta": data["tipo"],
                "estado": "activa"
            }
        )
        cuentas.append(cuenta)
        if created:
            print(f"✅ Cuenta creada: {cuenta.nro_cuenta} - {cuenta.moneda.codigo} para {cuenta.cliente.nombre}")
    
    return cuentas

# Crear tasas de cambio
def crear_tasas_cambio(monedas):
    tasas_data = [
        {"origen": "USD", "destino": "PYG", "tasa": 7300.00},
        {"origen": "PYG", "destino": "USD", "tasa": 0.000137},
        {"origen": "EUR", "destino": "PYG", "tasa": 7800.00},
        {"origen": "PYG", "destino": "EUR", "tasa": 0.000128},
        {"origen": "USD", "destino": "EUR", "tasa": 0.92},
        {"origen": "EUR", "destino": "USD", "tasa": 1.09},
        {"origen": "BRL", "destino": "USD", "tasa": 0.20},
        {"origen": "USD", "destino": "BRL", "tasa": 5.00},
        {"origen": "ARS", "destino": "USD", "tasa": 0.001},
        {"origen": "USD", "destino": "ARS", "tasa": 1000.00},
    ]
    
    for data in tasas_data:
        tasa, created = TasaCambio.objects.get_or_create(
            moneda_origen=monedas[data["origen"]],
            moneda_destino=monedas[data["destino"]],
            defaults={"tasa": Decimal(str(data["tasa"]))}
        )
        if created:
            print(f"✅ Tasa de cambio creada: {data['origen']} -> {data['destino']} = {data['tasa']}")

# Crear comisiones
def crear_comisiones():
    comisiones_data = [
        {"tipo": "debito", "porcentaje": 0.5, "monto_fijo": 5000},  # 0.5% + 5000 PYG
        {"tipo": "credito", "porcentaje": 0.0, "monto_fijo": 0},   # Sin comisión
        {"tipo": "transferencia", "porcentaje": 1.0, "monto_fijo": 10000},  # 1% + 10000 PYG
    ]
    
    for data in comisiones_data:
        comision, created = Comision.objects.get_or_create(
            tipo_transaccion=data["tipo"],
            defaults={
                "porcentaje": Decimal(str(data["porcentaje"])),
                "monto_fijo": Decimal(str(data["monto_fijo"]))
            }
        )
        if created:
            print(f"✅ Comisión creada: {data['tipo']} - {data['porcentaje']}% + {data['monto_fijo']}")

# Crear transacciones de ejemplo
def crear_transacciones(cuentas):
    tipos = ["debito", "credito", "transferencia"]
    estados = ["pendiente", "completada", "fallida"]
    
    transacciones_creadas = 0
    
    for cuenta in cuentas:
        # Crear entre 3 y 8 transacciones por cuenta
        num_transacciones = random.randint(3, 8)
        
        for _ in range(num_transacciones):
            tipo = random.choice(tipos)
            monto = Decimal(str(round(random.uniform(50, 1000), 2)))
            estado = random.choice(estados) if random.random() > 0.8 else "completada"  # 80% completadas
            
            # Para transferencias, elegir una cuenta destino diferente
            cuenta_destino = None
            if tipo == "transferencia":
                cuentas_disponibles = [c for c in cuentas if c != cuenta and c.moneda == cuenta.moneda]
                if cuentas_disponibles:
                    cuenta_destino = random.choice(cuentas_disponibles)
                else:
                    tipo = "debito"  # Cambiar a débito si no hay cuentas compatibles
            
            transaccion = Transaccion.objects.create(
                cuenta=cuenta,
                cuenta_destino=cuenta_destino,
                monto=monto,
                tipo=tipo,
                estado=estado,
                fecha=timezone.now() - timedelta(days=random.randint(0, 30)),
                referencia=f"REF{random.randint(100000, 999999)}",
                motivo=f"{'Pago de servicios' if tipo == 'debito' else 'Depósito en cuenta' if tipo == 'credito' else 'Transferencia entre cuentas'}",
                descripcion=f"Transacción {tipo} por {monto} {cuenta.moneda.codigo}"
            )
            transacciones_creadas += 1
    
    print(f"✅ {transacciones_creadas} transacciones creadas")

if __name__ == "__main__":
    print("🚀 Iniciando población de base de datos...")
    
    # Crear datos maestros
    monedas = crear_monedas()
    entidades = crear_entidades()
    
    # Crear clientes y sus cuentas
    clientes = crear_clientes()
    cuentas = crear_cuentas(clientes, monedas, entidades)
    
    # Crear tasas de cambio y comisiones
    crear_tasas_cambio(monedas)
    crear_comisiones()
    
    # Crear transacciones de ejemplo
    crear_transacciones(cuentas)
    
    print("✅ Base de datos poblada exitosamente!")
    print(f"📊 Resumen:")
    print(f"   - {len(monedas)} monedas")
    print(f"   - {len(entidades)} entidades bancarias")
    print(f"   - {len(clientes)} clientes")
    print(f"   - {len(cuentas)} cuentas")
    print(f"   - {TasaCambio.objects.count()} tasas de cambio")
    print(f"   - {Comision.objects.count()} tipos de comisión")
    print(f"   - {Transaccion.objects.count()} transacciones")