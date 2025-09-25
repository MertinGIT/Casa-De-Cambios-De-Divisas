from decimal import Decimal, ROUND_DOWN
from django import forms
from .models import TasaDeCambio
from monedas.models import Moneda
from decimal import Decimal, ROUND_HALF_UP

class TasaDeCambioForm(forms.ModelForm):
    """
    Formulario para la creación y edición de tasas de cambio.

    Valida los montos de compra y venta asegurando:
        - Máximo 15 dígitos antes de la coma.
        - Máximo 8 decimales.
        - Redondeo a 2 decimales usando ROUND_HALF_UP.
    
    También valida que la moneda de origen y destino no sean iguales.

    Campos:
        - moneda_origen (Moneda): Moneda base, fijada por defecto a Guaraní (PYG).
        - moneda_destino (Moneda): Moneda destino, excluyendo la moneda base.
        - monto_compra (Decimal): Valor de compra, validado y redondeado.
        - monto_venta (Decimal): Valor de venta, validado y redondeado.
        - vigencia (DateTime): Fecha y hora de vigencia de la tasa.
        - estado (Boolean): Estado activo/inactivo de la tasa.

    Métodos de limpieza:
        - clean_monto_compra(): valida y redondea monto_compra.
        - clean_monto_venta(): valida y redondea monto_venta.
        - clean(): valida que moneda_origen y moneda_destino sean distintas.
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
    comision_compra = forms.DecimalField(
        max_digits=23,
        decimal_places=8,
        required=False,
        widget=forms.NumberInput(attrs={"step": "any", "class": "custom-input"})
    )
    comision_venta = forms.DecimalField(
        max_digits=23,
        decimal_places=8,
        required=False,
        widget=forms.NumberInput(attrs={"step": "any", "class": "custom-input"})
    )
    
    vigencia = forms.DateTimeField(
        input_formats=["%d/%m/%Y %H:%M", "%Y-%m-%d %H:%M"],  # <-- acepta ambos
        widget=forms.DateTimeInput(
            format="%d/%m/%Y %H:%M",
            attrs={
                "class": "custom-input",
                "id": "id_vigencia",
                "placeholder": "dd/mm/aaaa hh:mm"
            }
        )
    )

    def clean_monto_compra(self):
        """
        Valida y redondea el monto de compra.

        - Verifica que la parte entera tenga máximo 15 dígitos.
        - Verifica que la parte decimal tenga máximo 8 dígitos significativos.
        - Redondea el valor a 2 decimales usando ROUND_HALF_UP.

        """
        monto = self.cleaned_data["monto_compra"]
        if monto is not None:
            # Validar dígitos antes y después de la coma
            str_monto = f"{monto:.2f}"  # convierte a string con 8 decimales
            print("stringggggggggggggggggggggcompra",type(monto),flush=True)  # <class 'int'>
            entero, decimal = str_monto.split(".")
            if len(entero) > 15:
                raise forms.ValidationError("Máximo 15 dígitos antes de la coma.")
            if len(decimal.rstrip("0")) > 8:
                raise forms.ValidationError("Máximo 8 decimales.")
            # Redondear a 2 decimales
            monto = monto.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return monto

    def clean_monto_venta(self):
        """
        Valida y redondea el monto de venta.

        - Verifica que la parte entera tenga máximo 15 dígitos.
        - Verifica que la parte decimal tenga máximo 8 dígitos significativos.
        - Redondea el valor a 2 decimales usando ROUND_HALF_UP.

        """
        monto = self.cleaned_data["monto_venta"]
        if monto is not None:
            str_monto = f"{monto:.2f}"
            print("stringggggggggggggggggggggventa",type(monto),flush=True)  # <class 'int'>
            entero, decimal = str_monto.split(".")
            if len(entero) > 15:
                raise forms.ValidationError("Máximo 15 dígitos antes de la coma.")
            if len(decimal.rstrip("0")) > 8:
                raise forms.ValidationError("Máximo 8 decimales.")
            monto = monto.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return monto

    def clean_comision_compra(self):
        """
        Valida y redondea la comisión de compra.

        - Verifica que la comisión no sea negativa.
        - Redondea el valor a 2 decimales usando ROUND_HALF_UP.

        """
        comision = self.cleaned_data.get("comision_compra")
        if comision is not None:
            if comision < 0:
                raise forms.ValidationError("La comisión de compra no puede ser negativa.")
            comision = comision.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return comision

    def clean_comision_venta(self):
        """
        Valida y redondea la comisión de venta.

        - Verifica que la comisión no sea negativa.
        - Redondea el valor a 2 decimales usando ROUND_HALF_UP.

        """
        comision = self.cleaned_data.get("comision_venta")
        if comision is not None:
            if comision < 0:
                raise forms.ValidationError("La comisión de venta no puede ser negativa.")
            comision = comision.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return comision

    def clean(self):
        """
        Valida que la moneda de origen y destino no sean iguales.

        :return: Diccionario con los datos limpios.
        :rtype: dict
        :raises ValidationError: Si moneda_origen y moneda_destino son iguales.
        """
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
        fields = ['moneda_origen', 'moneda_destino', 'monto_compra', 'monto_venta', 'comision_compra', 'comision_venta', 'vigencia', 'estado']
        labels = {
            "moneda_origen": "Moneda Origen",
            "moneda_destino": "Moneda Destino",
            "monto_compra": "Compra",
            "monto_venta": "Venta",
            "comision_compra": "Comisión Compra",
            "comision_venta": "Comisión Venta",
            "vigencia": "Vigencia",
        }
        widgets = {
            "moneda_origen": forms.Select(attrs={"class": "custom-input", "id": "id_moneda_origen"}),
            "moneda_destino": forms.Select(attrs={"class": "custom-input", "id": "id_moneda_destino"}),
            "comision_compra": forms.NumberInput(attrs={"step": "any", "class": "custom-input"}),
            "comision_venta": forms.NumberInput(attrs={"step": "any", "class": "custom-input"}),
        }

    def __init__(self, *args, **kwargs):
        """
        Inicializa el formulario.

        - Fija moneda_origen por defecto a Guaraní (PYG) y la deshabilita.
        - Configura moneda_destino excluyendo la moneda base.
        """
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

