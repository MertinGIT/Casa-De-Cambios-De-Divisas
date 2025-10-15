Notificaciones
==============

El módulo notificaciones se encarga de enviar avisos automáticos a los usuarios cuando ocurre un cambio relevante en las tasas de cambio de monedas.


Modelos
-------
.. autoclass:: notificaciones.models.NotificacionMoneda
.. autoclass:: notificaciones.models.AuditoriaTasaCambio

Vistas
------
.. autofunction:: notificaciones.views.panel_alertas
.. autofunction:: notificaciones.views.guardar_configuracion
.. autofunction:: notificaciones.views.set_cliente_operativo

Eventos de señal
----------------
.. autofunction:: notificaciones.signals.capturar_valores_anteriores
.. autofunction:: notificaciones.signals.notificar_tasa_mas_actual
.. autofunction:: notificaciones.signals.notificar_cambio_tasa


Consumidores
------------
.. autoclass:: notificaciones.consumers.NotificacionConsumer
    :members:
    :undoc-members:
    :show-inheritance: