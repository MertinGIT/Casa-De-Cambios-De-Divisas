Roles y Permisos
================

Esta aplicación gestiona los roles y permisos de los usuarios en el sistema.

Modelos
-------
.. autoclass:: roles_permisos.models.GroupProfile
   :members:
   :undoc-members:
   :show-inheritance:
   :noindex: 

Formularios
-----------
.. autoclass:: roles_permisos.forms.RolForm
   :members:
   :undoc-members:
   :show-inheritance:
   :exclude-members: base_fields, declared_fields, Meta  

Vistas
------
.. autofunction:: roles_permisos.views.rol_lista
.. autofunction:: roles_permisos.views.rol_nuevo
.. autofunction:: roles_permisos.views.rol_editar
.. autofunction:: roles_permisos.views.rol_eliminar
.. autofunction:: roles_permisos.views.rol_detalle
.. autofunction:: roles_permisos.views.rol_activar
.. autofunction:: roles_permisos.views.rol_desactivar
