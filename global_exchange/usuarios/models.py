# usuarios/models.py
from django.contrib.auth.models import AbstractUser, Group
from django.db import models
from django.contrib.auth.validators import UnicodeUsernameValidator

class CustomUser(AbstractUser):
    """
    Modelo de usuario personalizado para el sistema Global Exchange.

    Hereda de `AbstractUser` y agrega campos específicos del proyecto.
    
    **Atributos:**
        - **username** (str): Nombre de usuario único (heredado de AbstractUser).
        - **email** (str): Correo electrónico del usuario (heredado).
        - **cedula** (str): Número de cédula único del usuario.
        - **rol** (Rol): Relación con el rol del usuario, permite definir permisos y tipo de usuario.

    """
    username = models.CharField(
        max_length=150,
        unique=True,
        validators=[UnicodeUsernameValidator()],
        error_messages={
            'unique': 'Ya existe un usuario con ese nombre.',
            'blank': 'Debes ingresar un nombre de usuario.',
        },
        help_text='Requerido. Hasta 150 caracteres. Letras, números y @/./+/-/_ solamente.',
        verbose_name='Nombre de usuario'
    )    
    # Eliminamos first_name y last_name si no los vamos a usar
    first_name = None
    last_name = None
    # Nuevo campo
    cedula = models.CharField(max_length=20,unique=True,error_messages={'unique': 'Ya existe un usuario con esta cédula.','blank': 'La cédula es obligatoria.', 'null': 'La cédula no puede ser nula.'}
    )
    def __str__(self):
        """Retorna el nombre de usuario como string representativo."""
        return self.username
