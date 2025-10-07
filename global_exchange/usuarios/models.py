# usuarios/models.py
from django.contrib.auth.models import AbstractUser, Group
from django.db import models
from django.contrib.auth.validators import UnicodeUsernameValidator
import pyotp


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
    cedula = models.CharField(max_length=20, unique=True, error_messages={'unique': 'Ya existe un usuario con esta cédula.', 'blank': 'La cédula es obligatoria.', 'null': 'La cédula no puede ser nula.'}
                              )
     # Campo para MFA
    mfa_secret = models.CharField(max_length=32, blank=True, null=True)
    mfa_transacciones = models.BooleanField(default=False)

    def __str__(self):
        """Retorna el nombre de usuario como string representativo."""
        return self.username

    def generate_mfa_secret(self):
        """Genera un secreto TOTP y lo guarda en el usuario."""
        if not self.mfa_secret:
            self.mfa_secret = pyotp.random_base32()
            self.save()
        return self.mfa_secret

# usuarios/models.py
from django.db import models
from django.conf import settings
import secrets

class BackupCode(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="backup_codes")
    code = models.CharField(max_length=12, unique=True)  # ej: XK9Q-Z8WT
    used = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} - {self.code} ({'usado' if self.used else 'activo'})"

    @staticmethod
    def generate_codes(user, count=6):
        codes = []
        for _ in range(count):
            code = f"{secrets.token_hex(4).upper()}"  # ejemplo: 'A3F9C1B2'
            formatted = f"{code[:4]}-{code[4:]}"      # 'A3F9-C1B2'
            backup = BackupCode.objects.create(user=user, code=formatted)
            codes.append(formatted)
        return codes
