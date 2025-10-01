from django.db.models.signals import post_save
from django.dispatch import receiver
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from decimal import Decimal
from datetime import datetime
from cotizaciones.models import TasaDeCambio
from notificaciones.models import NotificacionMoneda

UMBRAL_CAMBIO = Decimal('0.01')  # 1% de cambio mínimo


@receiver(post_save, sender=TasaDeCambio)
def notificar_cambio_tasa(sender, instance, created, **kwargs):
    """
    Detecta cambios en las tasas de cambio y notifica SOLO a los usuarios
    que tienen activa la notificación para esa moneda específica.
    """
    if created:
        return

    # Buscar la tasa anterior
    tasa_anterior = (
        TasaDeCambio.objects
        .filter(moneda_origen=instance.moneda_origen, moneda_destino=instance.moneda_destino)
        .exclude(pk=instance.pk)
        .order_by('-fecha_actualizacion')
        .first()
    )
    
    if not tasa_anterior:
        return

    # Calcular el porcentaje de cambio
    cambio_precio = abs((instance.precio_base - tasa_anterior.precio_base) / tasa_anterior.precio_base * 100)
    
    if cambio_precio < UMBRAL_CAMBIO:
        return

    # Obtener SOLO los usuarios que tienen activa la notificación para esta moneda
    usuarios_activos = NotificacionMoneda.objects.filter(
        moneda=instance.moneda_origen,
        activa=True
    ).select_related('user')

    if not usuarios_activos.exists():
        print(f"⚠️ No hay usuarios con notificaciones activas para {instance.moneda_origen.abreviacion}")
        return

    channel_layer = get_channel_layer()

    # Enviar notificación a cada usuario que tiene activa esta moneda
    for notificacion in usuarios_activos:
        user = notificacion.user
        group_name = f"notificaciones_user_{user.id}"
        
        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                'type': 'notificar_cambio_tasa',
                'moneda': instance.moneda_destino.abreviacion,
                'precio_anterior': float(tasa_anterior.precio_base),
                'precio_nuevo': float(instance.precio_base),
                'porcentaje_cambio': float(cambio_precio),
                'timestamp': datetime.now().isoformat()
            }
        )

    print(f"✅ Notificación enviada a {usuarios_activos.count()} usuario(s) para {instance.moneda_origen.abreviacion} ({cambio_precio:.2f}%)")