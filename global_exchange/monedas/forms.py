from django import forms
from .models import Moneda

class MonedaForm(forms.ModelForm):
    class Meta:
        model = Moneda
        fields = ['nombre', 'abreviacion']

    # Validación para 'nombre'
    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre')
        if any(char.isdigit() for char in nombre):
            raise forms.ValidationError("El nombre no puede contener números.")
        return nombre

    # Validación para 'abreviacion'
    def clean_abreviacion(self):
        abreviacion = self.cleaned_data.get('abreviacion')
        if any(char.isdigit() for char in abreviacion):
            raise forms.ValidationError("La abreviación no puede contener números.")
        return abreviacion  