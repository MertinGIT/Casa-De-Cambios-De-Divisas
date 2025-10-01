from django import forms
from .models import LimiteTransaccion
from decimal import Decimal, InvalidOperation


class LimiteTransaccionForm(forms.ModelForm):
    """
    Formulario para crear o editar el límite global de transacciones.
    - Solo hay una instancia en la BD.
    - Los límites se definen en la moneda base.
    """

    limite_diario = forms.DecimalField(
        max_digits=20,
        decimal_places=8,
        widget=forms.NumberInput(attrs={"step": "any", "class": "form-control custom-input"})
    )

    limite_mensual = forms.DecimalField(
        max_digits=20,
        decimal_places=8,
        widget=forms.NumberInput(attrs={"step": "any", "class": "form-control custom-input"})
    )

    class Meta:
        model = LimiteTransaccion
        fields = ['limite_diario', 'limite_mensual']
        widgets = {
            'moneda': forms.Select(attrs={'class': 'form-control custom-input'}),
        }

    def clean_limite_diario(self):
        """Validación del límite diario (>= 0)"""
        valor = self.cleaned_data.get('limite_diario')

        if isinstance(valor, Decimal):
            if valor < 0:
                raise forms.ValidationError("El límite diario debe ser mayor o igual a 0")
            return valor

        raw_value = self.data.get('limite_diario', '')
        if not raw_value.strip():
            raise forms.ValidationError("El límite diario es requerido")

        try:
            clean_value = str(raw_value).replace(',', '.')
            decimal_value = Decimal(clean_value)
            if decimal_value < 0:
                raise forms.ValidationError("El límite diario debe ser mayor o igual a 0")
            return decimal_value
        except (InvalidOperation, ValueError):
            raise forms.ValidationError(f"Valor inválido para límite diario: '{raw_value}'")

    def clean_limite_mensual(self):
        """Validación del límite mensual (>= 0)"""
        valor = self.cleaned_data.get('limite_mensual')

        if isinstance(valor, Decimal):
            if valor < 0:
                raise forms.ValidationError("El límite mensual debe ser mayor o igual a 0")
            return valor

        raw_value = self.data.get('limite_mensual', '')
        if not raw_value.strip():
            raise forms.ValidationError("El límite mensual es requerido")

        try:
            clean_value = str(raw_value).replace(',', '.')
            decimal_value = Decimal(clean_value)
            if decimal_value < 0:
                raise forms.ValidationError("El límite mensual debe ser mayor o igual a 0")
            return decimal_value
        except (InvalidOperation, ValueError):
            raise forms.ValidationError(f"Valor inválido para límite mensual: '{raw_value}'")

    def clean(self):
        """Validación de consistencia: mensual >= diario"""
        cleaned_data = super().clean()
        limite_diario = cleaned_data.get('limite_diario')
        limite_mensual = cleaned_data.get('limite_mensual')

        if limite_diario is not None and limite_mensual is not None:
            if limite_mensual < limite_diario:
                raise forms.ValidationError("El límite mensual no puede ser menor al límite diario.")

        return cleaned_data
