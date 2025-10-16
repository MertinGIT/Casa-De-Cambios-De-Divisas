from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from notificaciones.models import NotificacionMoneda


class NotificacionConsumer(AsyncJsonWebsocketConsumer):
    """
    Consumer WebSocket responsable de gestionar las conexiones en tiempo real
    para enviar notificaciones de cambios en las tasas de cambio a los usuarios.
    
    Cada usuario autenticado se conecta a un grupo único basado en su ID, 
    lo que permite enviar notificaciones personalizadas sin interferir 
    con otros usuarios conectados.
    """
    async def connect(self):
        """
        Establece la conexión WebSocket para el usuario autenticado.
        Si el usuario no está autenticado, la conexión se cierra inmediatamente.
        """
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
        """
        Maneja la desconexión del WebSocket eliminando al usuario de su grupo
        para liberar recursos y evitar envíos futuros de notificaciones.
        """
        # Remover del grupo personal
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def notificar_cambio_tasa(self, event):
        """
        Envía una notificación JSON al usuario sobre un cambio de tasa de cambio.
        
        Solo se envía si el usuario tiene activada la notificación para la moneda 
        afectada. Los datos incluyen los precios anterior y nuevo, el porcentaje de 
        cambio, el tipo de actualización y si se trata de una nueva tasa.
        """
        moneda = event.get("moneda")
        
        tiene_activa = await self.usuario_tiene_notificacion_activa(moneda)
        
        if tiene_activa:
            await self.send_json({
                "type": "notificar_cambio_tasa",
                "moneda": moneda,
                "precio_anterior": event.get("precio_anterior"),
                "precio_nuevo": event.get("precio_nuevo"),
                "porcentaje_cambio": event.get("porcentaje_cambio"),
                "es_nueva": event.get("es_nueva", False),
                "tipo_cambio": event.get("tipo_cambio", "EDICION"),
            })

    @database_sync_to_async
    def usuario_tiene_notificacion_activa(self, moneda_abreviacion):
        """
        Comprueba en la base de datos si el usuario tiene activadas las notificaciones
        para una moneda específica.
        
        Retorna:
            bool: True si la notificación está activa, False en caso contrario.
        """
        return NotificacionMoneda.objects.filter(
            user=self.user,
            moneda__abreviacion=moneda_abreviacion,
            activa=True
        ).exists()