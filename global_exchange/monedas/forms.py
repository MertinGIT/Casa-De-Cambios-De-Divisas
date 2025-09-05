from django import forms
from .models import Moneda

class MonedaForm(forms.ModelForm):
    """
    Formulario basado en el modelo `Moneda` que permite crear y actualizar registros
    de monedas dentro del sistema.

    Campos:
        - nombre (CharField): Nombre de la moneda (ejemplo: Dólar, Euro).
        - abreviacion (CharField): Abreviatura oficial de la moneda (ejemplo: USD, EUR).

    Validaciones:
        - clean_nombre:
            Evita que el nombre contenga números.
            Si se encuentra un dígito, se lanza una ValidationError.
        - clean_abreviacion:
            Evita que la abreviación contenga números.
            Si se encuentra un dígito, se lanza una ValidationError.
    """
    class Meta:
        model = Moneda
        fields = ['nombre', 'abreviacion']

    # Validación para 'nombre'
    def clean_nombre(self):
        """
        Valida que el campo 'nombre' no contenga números.
        :return: nombre limpio si es válido.
        :raises forms.ValidationError: si se detecta algún número.
        """
        nombre = self.cleaned_data.get('nombre')
        if any(char.isdigit() for char in nombre):
            raise forms.ValidationError("El nombre no puede contener números.")
        return nombre

    # Validación para 'abreviacion'
    def clean_abreviacion(self):
        """
        Valida que el campo 'abreviacion' no contenga números.
        :return: abreviacion limpia si es válida.
        :raises forms.ValidationError: si se detecta algún número.
        """
        abreviacion = self.cleaned_data.get('abreviacion')
        if any(char.isdigit() for char in abreviacion):
            raise forms.ValidationError("La abreviación no puede contener números.")
        return abreviacion  