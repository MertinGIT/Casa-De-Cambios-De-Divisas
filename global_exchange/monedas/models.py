from django.db import models


class Moneda(models.Model):
    """
    Modelo que representa una moneda dentro del sistema.

    Atributos:
        nombre (CharField):
            Nombre completo de la moneda (ejemplo: "Dólar", "Euro").
            - Máximo: 100 caracteres
            - Debe ser único (unique=True).

        abreviacion (CharField):
            Abreviatura oficial de la moneda (ejemplo: "USD", "EUR").
            - Máximo: 10 caracteres
            - Debe ser única (unique=True).

        estado (BooleanField):
            Indica si la moneda está activa en el sistema.
            - True: activa
            - False: inactiva
            - Valor por defecto: True

    Métodos:
        __str__:
            Devuelve la representación legible de la moneda, usando su nombre.
            Ejemplo: "Dólar", "Euro".

    """

    nombre = models.CharField(max_length=100, unique=True)
    abreviacion = models.CharField(max_length=10, unique=True)
    estado = models.BooleanField(default=True)

    """
        Retorna el nombre de la moneda como representación de texto.
    """
    def __str__(self):
        return f"{self.nombre}"
