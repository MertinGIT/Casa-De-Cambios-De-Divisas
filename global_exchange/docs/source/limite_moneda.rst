Limite de Moneda
================

Esta aplicación gestiona los límites diarios y mensuales de operaciones en la moneda base (Guaraní), aplicables a todos los clientes del sistema

Modelos
-------
.. autoclass:: limite_moneda.models.LimiteTransaccion

Vistas
-------------------------
.. autofunction:: limite_moneda.views.lista_limites
.. autofunction:: limite_moneda.views.crear_limite
.. autofunction:: limite_moneda.views.editar_limite
.. autofunction:: limite_moneda.views.cambiar_estado_limite
.. autofunction:: limite_moneda.views.limite_detalle
