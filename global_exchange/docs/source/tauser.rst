Tauser
======

Esta aplicación gestiona el stock de efectivo de los dispositivos Tauser, incluyendo las denominaciones de billetes, movimientos de stock, reservas de efectivo y retiros asociados a transacciones.

Modelos
-------

.. autoclass:: tauser.models.Denominacion
.. autoclass:: tauser.models.Localidad
.. autoclass:: tauser.models.StockTauser
.. autoclass:: tauser.models.MovimientoStock
.. autoclass:: tauser.models.RetiroEfectivo
.. autoclass:: tauser.models.DetalleRetiroEfectivo
.. autoclass:: tauser.models.ReservaTauser
.. autoclass:: tauser.models.DetalleReservaTauser

Utilidades
----------

.. autoclass:: tauser.utils.GestorStockTauser
    :members:
    :undoc-members:
    :show-inheritance:

    Esta clase gestiona las operaciones principales del stock TAUSER:
    - Reserva y liberación de efectivo.
    - Retiros y depósitos físicos.
    - Aprovisionamiento de billetes.
    - Control de consistencia mediante transacciones atómicas.


Vistas
------

.. autofunction:: tauser.views.atm_seleccionar_localidad
.. autofunction:: tauser.views.atm_login
.. autofunction:: tauser.views.atm_logout
.. autofunction:: tauser.views.atm_transacciones
.. autofunction:: tauser.views.atm_depositar
.. autofunction:: tauser.views.atm_extraer