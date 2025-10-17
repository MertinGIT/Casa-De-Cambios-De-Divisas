Operaciones
===========

Sistema web que permite simular, registrar y gestionar transacciones de compra y venta de monedas. Incluye cálculo automático de tasas de cambio, aplicación de comisiones y descuentos por segmentación de clientes, control de límites, y conexión con servicios bancarios externos para procesar operaciones de manera segura.


Modelos
-------
.. autoclass:: operaciones.models.TransaccionQuerySet
.. autoclass:: operaciones.models.TransaccionManager
.. autoclass:: operaciones.models.Transaccion


Vistas basadas en función
------------------------
.. autofunction:: operaciones.views.simulador_operaciones
.. autofunction:: operaciones.views.obtener_clientes_usuario
.. autofunction:: operaciones.views.set_cliente_operativo
.. autofunction:: operaciones.views.verificar_tasa
.. autofunction:: operaciones.views.hora_servidor
.. autofunction:: operaciones.views.enviar_transaccion_al_banco
.. autofunction:: operaciones.views.guardar_metodo_pago
.. autofunction:: operaciones.views.guardar_transaccion 
.. autofunction:: operaciones.views.actualizar_estado_transaccion
.. autofunction:: operaciones.views.crear_pago_stripe
.. autofunction:: operaciones.views.enviar_pin
.. autofunction:: operaciones.views.validar_pin 
.. autofunction:: operaciones.views.obtener_metodos_pago 
.. autofunction:: operaciones.views.verificar_limites 



   