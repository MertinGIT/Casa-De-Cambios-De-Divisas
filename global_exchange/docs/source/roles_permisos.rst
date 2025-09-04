Roles y Permisos
================

Esta aplicación gestiona los roles y permisos de los usuarios en el sistema.

Modelos
-------
.. autoclass:: roles_permisos.models.Rol

.. autoclass:: roles_permisos.models.Permiso


Vistas
------
.. autofunction:: roles_permisos.views.superadmin_required
.. autofunction:: roles_permisos.views.rol_lista
.. autofunction:: roles_permisos.views.rol_nuevo
.. autofunction:: roles_permisos.views.rol_editar
.. autofunction:: roles_permisos.views.rol_eliminar
.. autofunction:: roles_permisos.views.rol_detalle

Formularios
-----------
.. autoclass:: roles_permisos.forms.RolForm
   :exclude-members: base_fields, declared_fields 


