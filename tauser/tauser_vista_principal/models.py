# tauser_vista_principal/models.py
from django.db import models
from django.contrib.auth.models import User

class MachineStock(models.Model):
    """
    Representa el stock de máquinas disponibles.
    """
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    quantity = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.quantity} unidades"


class AuditLog(models.Model):
    """
    Registro de auditoría para movimientos de stock.
    """
    ACTION_CHOICES = [
        ("ADD", "Agregado"),
        ("REMOVE", "Retirado"),
        ("UPDATE", "Actualizado"),
    ]

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    machine = models.ForeignKey(MachineStock, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=10, choices=ACTION_CHOICES)
    quantity = models.IntegerField()
    timestamp = models.DateTimeField(auto_now_add=True)
    note = models.TextField(blank=True)

    def __str__(self):
        user_str = self.user.username if self.user else "Sistema"
        machine_str = self.machine.name if self.machine else "Desconocido"
        return f"[{self.timestamp}] {user_str} {self.action} {self.quantity} de {machine_str}"
