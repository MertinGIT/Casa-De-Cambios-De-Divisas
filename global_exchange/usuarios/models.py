# usuarios/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    # Eliminamos first_name y last_name si no los vamos a usar
    first_name = None
    last_name = None

    # Nuevo campo
    cedula = models.CharField(max_length=20, unique=True, null=False, blank=False)

    def __str__(self):
        return self.username
