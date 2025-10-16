# pagos/signals.py
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from .models import MetodoPago

@receiver(post_migrate)
def crear_efectivo(sender,app_config, **kwargs):
    if app_config.name == 'metodos_pagos':  # Solo ejecutar para tu app
        MetodoPago.objects.get_or_create(
            nombre='Efectivo',
            defaults={'descripcion': 'Pago en efectivo', 'activo': True}
        )
