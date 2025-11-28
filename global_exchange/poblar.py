import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'global_exchange.settings')
django.setup()

from monedas.models import Moneda
from tauser.models import Denominacion, StockTauser, Localidad

# Diccionario de denominaciones por moneda
denominaciones_por_moneda = {
    'PYG': [2000, 5000, 10000, 20000, 50000, 100000],
    'USD': [1, 5, 10, 20, 50, 100],
}

STOCK_INICIAL = 50  # Cantidad inicial de billetes por denominación

print("\n" + "="*50)
print("POBLANDO DENOMINACIONES Y STOCK POR LOCALIDAD")
print("="*50)

#  Obtener todas las localidades activas
localidades = Localidad.objects.filter(activo=True)

if not localidades.exists():
    print(" ERROR: No hay localidades creadas. Ejecuta primero poblar.py")
    exit()

print(f"\n Localidades encontradas: {localidades.count()}")
for loc in localidades:
    print(f"   - {loc.nombre}")

print("\n" + "-"*50)

for abreviacion_moneda, valores in denominaciones_por_moneda.items():
    try:
        moneda = Moneda.objects.get(abreviacion=abreviacion_moneda)
        print(f"\n Procesando moneda: {moneda.nombre} ({abreviacion_moneda})")
    except Moneda.DoesNotExist:
        print(f" No existe la moneda {abreviacion_moneda}, se la debe crear primero.")
        continue

    # Crear denominaciones (solo una vez por moneda)
    print(f"    Creando denominaciones para {abreviacion_moneda}...")
    for valor in valores:
        denom, created = Denominacion.objects.get_or_create(
            moneda=moneda,
            valor=Decimal(valor),
            defaults={'activo': True}
        )
        if created:
            print(f"       Denominación creada: {valor} {abreviacion_moneda}")
        else:
            print(f"      ℹ Denominación ya existía: {valor} {abreviacion_moneda}")

    # Crear stock para CADA localidad
    print(f"   🏦 Asignando stock a localidades...")
    denominaciones = Denominacion.objects.filter(moneda=moneda, activo=True)
    
    for localidad in localidades:
        print(f"\n       {localidad.nombre}:")
        for denom in denominaciones:
            stock, created_stock = StockTauser.objects.get_or_create(
                localidad=localidad,  # Filtro por localidad
                denominacion=denom,
                defaults={
                    'cantidad': STOCK_INICIAL,
                    'cantidad_minima': 10
                }
            )
            if created_stock:
                print(f"          Stock creado: {denom.valor} {abreviacion_moneda} → {STOCK_INICIAL} billetes")
            else:
                print(f"         ℹ️ Stock ya existía: {denom.valor} {abreviacion_moneda} → {stock.cantidad} billetes")

print("\n" + "="*50)
print("✅ DENOMINACIONES Y STOCK CONFIGURADOS")
print("="*50)
print(f"\nResumen:")
print(f"  - {Denominacion.objects.count()} denominaciones creadas")
print(f"  - {StockTauser.objects.count()} registros de stock creados")
print(f"  - {localidades.count()} localidades con stock asignado")
print("="*50)