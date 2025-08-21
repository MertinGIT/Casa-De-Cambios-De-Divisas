from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()
class Permiso(models.Model):
    nombre = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.nombre

class Rol(models.Model):
    nombre = models.CharField(max_length=50, unique=True)
    descripcion = models.TextField(blank=True)
    permisos = models.ManyToManyField(Permiso, blank=True)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name="usuarios", null=True)
    def __str__(self):
        return self.nombre