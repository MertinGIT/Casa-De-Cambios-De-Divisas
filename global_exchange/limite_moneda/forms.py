from django import forms
from .models import LimiteTransaccion
from clientes.models import Cliente
from monedas.models import Moneda

class LimiteTransaccionForm(forms.ModelForm):
    """
    Formulario para crear o editar límites de transacción.

    Funcionalidades:
        - Selección dinámica de clientes activos.
        - Selección dinámica de monedas activas.
        - Validación de que el límite mensual no sea menor al diario.
    """
    class Meta:
        model = LimiteTransaccion
        fields = ['cliente', 'moneda', 'limite_diario', 'limite_mensual']
        widgets = {
            'cliente': forms.Select(attrs={'class': 'form-control custom-input'}),
            'moneda': forms.Select(attrs={'class': 'form-control custom-input'}),
            'limite_diario': forms.NumberInput(attrs={
                'class': 'form-control custom-input',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
            'limite_mensual': forms.NumberInput(attrs={
                'class': 'form-control custom-input',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
        }

    def __init__(self, *args, **kwargs):
        """Inicialización personalizada: crear choices dinámicos para clientes y monedas"""
        super().__init__(*args, **kwargs)

        # Clientes activos
        clientes = Cliente.objects.filter(estado='activo')
        cliente_choices = [('', 'Seleccione un cliente...')]
        cliente_choices += [(c.id, c.nombre) for c in clientes]
        self.fields['cliente'].widget.choices = cliente_choices

        # Monedas activas
        monedas = Moneda.objects.filter(estado=True)
        moneda_choices = [('', 'Seleccione una moneda...')]
        moneda_choices += [(m.id, f"{m.nombre} ({m.abreviacion})") for m in monedas]
        self.fields['moneda'].widget.choices = moneda_choices

    def clean(self):
        """Validación de consistencia entre límites diario y mensual"""
        cleaned_data = super().clean()
        limite_diario = cleaned_data.get('limite_diario')
        limite_mensual = cleaned_data.get('limite_mensual')

        if limite_diario and limite_mensual and limite_mensual < limite_diario:
            raise forms.ValidationError("El límite mensual no puede ser menor al límite diario.")

        return cleaned_data
