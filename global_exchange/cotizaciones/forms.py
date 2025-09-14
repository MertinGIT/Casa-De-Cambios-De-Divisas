from decimal import Decimal, ROUND_DOWN
from django import forms
from .models import TasaDeCambio
from monedas.models import Moneda
from decimal import Decimal, ROUND_HALF_UP

class TasaDeCambioForm(forms.ModelForm):
    """
    Formulario para la creación y edición de tasas de cambio.
    """

    monto_compra = forms.DecimalField(
        max_digits=23,
        decimal_places=8,
        required=True,
        widget=forms.NumberInput(attrs={"step":  "any"})  # <-- importante
    )
    monto_venta = forms.DecimalField(
        max_digits=23,
        decimal_places=8,
        required=True,
        widget=forms.NumberInput(attrs={"step":  "any"})  # <-- importante
    )
    def clean_monto_compra(self):
        monto = self.cleaned_data["monto_compra"]
        if monto is not None:
            # Validar dígitos antes y después de la coma
            str_monto = f"{monto:.2f}"  # convierte a string con 8 decimales
            entero, decimal = str_monto.split(".")
            if len(entero) > 15:
                raise forms.ValidationError("Máximo 15 dígitos antes de la coma.")
            if len(decimal.rstrip("0")) > 8:
                raise forms.ValidationError("Máximo 8 decimales.")
            # Redondear a 2 decimales
            monto = monto.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return monto

    def clean_monto_venta(self):
        monto = self.cleaned_data["monto_venta"]
        if monto is not None:
            str_monto = f"{monto:.2f}"
            entero, decimal = str_monto.split(".")
            if len(entero) > 15:
                raise forms.ValidationError("Máximo 15 dígitos antes de la coma.")
            if len(decimal.rstrip("0")) > 8:
                raise forms.ValidationError("Máximo 8 decimales.")
            monto = monto.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return monto

    def clean(self):
        cleaned_data = super().clean()
        origen = cleaned_data.get("moneda_origen")
        destino = cleaned_data.get("moneda_destino")

        if origen and destino and origen == destino:
            raise forms.ValidationError(
                "La moneda base y la moneda destino no pueden ser iguales."
            )
        return cleaned_data

    class Meta:
        model = TasaDeCambio
        fields = ['moneda_origen', 'moneda_destino', 'monto_compra', 'monto_venta', 'vigencia', 'estado']
        labels = {
            "moneda_origen": "Moneda Origen",
            "moneda_destino": "Moneda Destino",
            "monto_compra": "Compra",
            "monto_venta": "Venta",
            "vigencia": "Vigencia",
        }
        widgets = {
            "moneda_origen": forms.Select(attrs={"class": "custom-input", "id": "id_moneda_origen"}),
            "moneda_destino": forms.Select(attrs={"class": "custom-input", "id": "id_moneda_destino"}),
            "vigencia": forms.DateTimeInput(attrs={"class": "custom-input", "id": "id_vigencia", "type": "datetime-local"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        guarani, created = Moneda.objects.get_or_create(
            abreviacion='PYG',
            defaults={'nombre': 'Guaraní'}
        )
        self.fields['moneda_origen'].initial = guarani
        self.fields['moneda_origen'].disabled = True  
        # Quitar del select de destino la moneda base
        self.fields['moneda_destino'].queryset = Moneda.objects.filter(
        estado=True
        ).exclude(pk=guarani.pk)

