import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'global_exchange.settings')
django.setup()

from metodos_pagos.models import MetodoPago
from medio_acreditacion.models import TipoEntidadFinanciera
from medio_acreditacion.models import MedioAcreditacion
from clientes.models import Cliente
from monedas.models import Moneda

# --- Moneda por defecto ---
moneda, created = Moneda.objects.get_or_create(
    id=1,
    defaults={
        'nombre': 'Guaraní',
        'abreviacion': 'PYG',
        'estado': True
    }
)
if created:
    print("✅ Moneda 'Guaraní (PYG)' creada.")
else:
    print("ℹ️ Moneda 'Guaraní (PYG)' ya existía.")
    
# --- Método de Pago por defecto ---
metodo, created = MetodoPago.objects.get_or_create(
    id=1,
    defaults={
        'nombre': 'Efectivo',
        'descripcion': 'Pago en efectivo',
        'activo': True,
        'comision': Decimal('5.00')
    }
)
if created:
    print("✅ Método de pago 'Efectivo' creado.")
else:
    print("ℹ️ Método de pago 'Efectivo' ya existía.")

# --- Entidad Financiera por defecto ---
entidad, created = TipoEntidadFinanciera.objects.get_or_create(
    id=0,
    defaults={
        'nombre': 'Tauser',
        'tipo': 'OTRO',
        'estado': True,
        'comision': Decimal('0.00')
    }
)
if created:
    print("✅ Entidad financiera 'Tauser' creada.")
else:
    print("ℹ️ Entidad financiera 'Tauser' ya existía.")

