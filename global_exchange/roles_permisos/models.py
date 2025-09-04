from django.db import models
from django.contrib.auth.models import Group

class GroupProfile(models.Model):
    group = models.OneToOneField(Group, on_delete=models.CASCADE, related_name='profile')
    estado = models.CharField(max_length=10, choices=[('Activo', 'Activo'), ('Inactivo', 'Inactivo')], default='Activo')

    def __str__(self):
        return f"{self.group.name} ({self.estado})"
