Segmentacion de clientes
=================================

Este módulo gestiona la segmentación de clientes según criterios de negocio.  
Permite clasificar a los clientes en grupos o segmentos, cada uno con características
específicas como descuentos, estado y descripción. Esto facilita aplicar políticas
comerciales diferenciadas y generar reportes por tipo de cliente.

Modelos
-------
.. autoclass:: cliente_segmentacion.models.Segmentacion

Vistas
------
.. autofunction:: cliente_segmentacion.views.lista_segmentaciones
.. autofunction:: cliente_segmentacion.views.crear_segmentacion
.. autofunction:: cliente_segmentacion.views.editar_segmentacion
.. autofunction:: cliente_segmentacion.views.cambiar_estado_segmentacion
.. autofunction:: cliente_segmentacion.views.segmentacion_detalle
.. autofunction:: cliente_segmentacion.views.check_nombre_segmentacion

