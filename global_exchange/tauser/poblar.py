from decimal import Decimal
from monedas.models import Moneda
from tauser.models import Denominacion, StockTauser

# Diccionario de denominaciones por moneda
denominaciones_por_moneda = {
    'PYG': [2000, 5000, 10000, 20000, 50000, 100000],
    'USD': [1, 5, 10, 20, 50, 100],
    'EUR': [5, 10, 20, 50, 100, 200, 500],  # Agregado euros
}

STOCK_INICIAL = 50  # Cantidad inicial de billetes por denominación

for abreviacion_moneda, valores in denominaciones_por_moneda.items():
    try:
        moneda = Moneda.objects.get(abreviacion=abreviacion_moneda)
    except Moneda.DoesNotExist:
        print(f"No existe la moneda {abreviacion_moneda}, se la debe crear primero.")
        continue

    for valor in valores:
        denom, created = Denominacion.objects.get_or_create(
            moneda=moneda,
            valor=Decimal(valor),
            defaults={'activo': True}
        )
        stock, created_stock = StockTauser.objects.get_or_create(
            denominacion=denom,
            defaults={'cantidad': STOCK_INICIAL}
        )
        if created_stock:
            print(f"Creado stock {valor} {abreviacion_moneda}: {STOCK_INICIAL} billetes")
