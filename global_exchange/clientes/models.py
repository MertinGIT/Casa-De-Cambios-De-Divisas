from django.db import models
class Segmentacion(models.Model):
    nombre = models.CharField(max_length=50, unique=True)
    descripcion = models.TextField(blank=True, null=True)
    descuento = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.0,
        help_text="Descuento en porcentaje para este tipo de cliente"
    )
    
class Cliente(models.Model):
    nombre = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    segmentacion = models.ForeignKey(Segmentacion, on_delete=models.PROTECT)

    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)