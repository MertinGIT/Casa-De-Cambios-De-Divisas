from django.core.management.base import BaseCommand
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync


class Command(BaseCommand):
    help = 'Envía una notificación de prueba al WebSocket'

    def handle(self, *args, **options):
        channel_layer = get_channel_layer()
        
        # Enviar notificación de prueba
        async_to_sync(channel_layer.group_send)(
            'notificaciones',
            {
                'type': 'notificar_cambio_tasa',
                'moneda': 'USD',
                'precio_anterior': 7000.00,
                'precio_nuevo': 7100.00,
                'porcentaje_cambio': 1.43,
            }
        )
        
        self.stdout.write(
            self.style.SUCCESS('✅ Notificación de prueba enviada')
        )