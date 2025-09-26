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
   

Formularios
-----------
.. autoclass:: usuarios.forms.CustomUserCreationForm

.. autoclass:: usuarios.forms.CustomUserChangeForm
