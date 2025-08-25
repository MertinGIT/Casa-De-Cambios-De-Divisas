Asignación de Clientes a Usuarios
=================================

Este modelo intermedio gestiona la relación entre los usuarios y los clientes.  
Permite registrar qué usuario está vinculado con qué cliente, y se utiliza en conjunto  
con los roles definidos en el sistema para administrar permisos y accesos.

Modelos
-------
.. autoclass:: asignar_clientes_usuarios.models.Usuario_Rol_Cliente
   :members: __str__
   :undoc-members:
   :show-inheritance:

Vistas
------
.. autofunction:: asignar_clientes_usuarios.views.lista_usuarios_roles
.. autofunction:: asignar_clientes_usuarios.views.crear_usuario_rol
.. autofunction:: asignar_clientes_usuarios.views.editar_usuario_rol
.. autofunction:: asignar_clientes_usuarios.views.eliminar_usuario_rol

