Usuarios
========

Aplicación que gestiona los usuarios, roles y permisos.

Modelos
-------
.. autoclass:: usuarios.models.CustomUser

Vistas
------
.. autofunction:: usuarios.views.home
.. autofunction:: usuarios.views.signup
.. autofunction:: usuarios.views.signin
.. autofunction:: usuarios.views.signout
.. autofunction:: usuarios.views.pagina_aterrizaje
.. autofunction:: usuarios.views.error_404_view
.. autofunction:: usuarios.views.editarPerfil
.. autofunction:: usuarios.views.crud_empleados
.. autofunction:: usuarios.views.activateEmail
.. autofunction:: usuarios.views.user_roles_lista
.. autofunction:: usuarios.views.user_roles_edit
.. autofunction:: usuarios.views.user_roles_detalle
.. autofunction:: usuarios.views.obtener_clientes_usuario
.. autofunction:: usuarios.views.set_cliente_operativo
.. autofunction:: usuarios.views.mfa_setup
.. autofunction:: usuarios.views.mfa_verify
.. autofunction:: usuarios.views.generate_qr    



Formularios
-----------
.. autoclass:: usuarios.forms.CustomUserCreationForm
.. autoclass:: usuarios.forms.CustomUserChangeForm
.. autoclass:: usuarios.forms.UserRolePermissionForm