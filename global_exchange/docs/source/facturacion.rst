Facturación
===========

Esta aplicación gestiona la generación, consulta y envío de facturas electrónicas, 
así como la administración de rangos de numeración asignada a la empresa y la integración con el servicio Factura Segura.


Modelos
-------

.. autoclass:: facturacion.models.RangoFacturacion
.. autoclass:: facturacion.models.Factura


Servicios
---------

.. autoclass:: facturacion.services.FacturaSeguraService
    :members:
    :undoc-members:
    :show-inheritance:

    Este servicio centraliza toda la comunicación con la API de **FacturaSegura**.
    Permite generar, calcular, consultar y descargar documentos electrónicos (facturas)
    en formato oficial, gestionando de forma automática los rangos de numeración
    asignada a la empresay garantizando la coherencia de las operaciones mediante transacciones atómicas.


Vistas
------

.. autofunction:: facturacion.views.facturacion_view
.. autofunction:: facturacion.views.generar_factura_transaccion
.. autofunction:: facturacion.views.consultar_estado_factura
.. autofunction:: facturacion.views.consultar_estado_factura_transaccion
.. autofunction:: facturacion.views.enviar_factura_email
.. autofunction:: facturacion.views.factura_resumida
.. autofunction:: facturacion.views.descargar_factura
.. autofunction:: facturacion.views.obtener_clientes_usuario
.. autofunction:: facturacion.views.set_cliente_operativo
