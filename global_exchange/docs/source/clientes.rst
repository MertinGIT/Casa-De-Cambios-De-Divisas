Clientes
========

Este módulo se encarga de gestionar la información relacionada con los clientes de la casa de cambios.

Modelos
-------
.. autoclass:: clientes.models.Segmentacion

.. autoclass:: clientes.models.Cliente

Vistas basadas en función
------------------------
.. autofunction:: clientes.views.clientes


Vistas basadas en clase
-----------------------
.. autoclass:: clientes.views.ClienteListView
   :members: get_queryset, get_context_data



.. autoclass:: clientes.views.ClienteCreateView
   :members: get_context_data



.. autoclass:: clientes.views.ClienteUpdateView
   :members: get_context_data



.. autoclass:: clientes.views.ClienteDeleteView
   :members: delete


   