Limite por Cientes y Monedas
===========

Esta aplicación gestiona los límites de transacciones por cliente y moneda dentro del sistema.


Modelos
-------
.. autoclass:: limite_moneda.models.LimiteTransaccion


Vistas basadas en función
------------------------
.. autofunction:: limite_moneda.views.check_nombre_cliente
.. autofunction:: limite_moneda.views.lista_limites
.. autofunction:: limite_moneda.views.crear_limite
.. autofunction:: limite_moneda.views.editar_limite
.. autofunction:: limite_moneda.views.cambiar_estado_limite
.. autofunction:: limite_moneda.views.limite_detalle
.. autofunction:: limite_moneda.views.get_monedas