from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from notificaciones.models import NotificacionMoneda


class NotificacionConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        # Obtener el usuario autenticado
        self.user = self.scope["user"]
        
        if self.user.is_anonymous:
            await self.close()
            return
        
        # Agregar al grupo personal del usuario
        self.group_name = f"notificaciones_user_{self.user.id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        
        await self.accept()
        await self.send_json({
            "type": "conexion",
            "mensaje": f"Conectado al sistema de notificaciones para {self.user.username}"
        })

    async def disconnect(self, close_code):
        # Remover del grupo personal
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def notificar_cambio_tasa(self, event):
        """
        Verifica si el usuario tiene activa la notificación para esta moneda
        antes de enviar el mensaje.
        """
        moneda = event.get("moneda")
        
        # Verificar si el usuario tiene activa la notificación para esta moneda
        tiene_activa = await self.usuario_tiene_notificacion_activa(moneda)
        
        if tiene_activa:
            await self.send_json({
                "type": "notificar_cambio_tasa",
                "moneda": moneda,
                "precio_anterior": event.get("precio_anterior"),
                "precio_nuevo": event.get("precio_nuevo"),
                "porcentaje_cambio": event.get("porcentaje_cambio"),
            })

    @database_sync_to_async
    def usuario_tiene_notificacion_activa(self, moneda_abreviacion):
        """
        Verifica si el usuario tiene configurada y activa la notificación
        para una moneda específica.
        """
        return NotificacionMoneda.objects.filter(
            user=self.user,
            moneda__abreviacion=moneda_abreviacion,
            activa=True
        ).exists()