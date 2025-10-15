from django import forms
from clientes.models import Cliente


class LoginATMForm(forms.Form):
    """Formulario para login en terminal de autoservicio"""
    cedula = forms.CharField(
        max_length=20,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Ingrese su número de cédula',
            'autofocus': True
        }),
        label='Número de Cédula'
    )

    def clean_cedula(self):
        cedula = self.cleaned_data.get('cedula')
        try:
            cliente = Cliente.objects.get(cedula=cedula, estado='activo')
        except Cliente.DoesNotExist:
            raise forms.ValidationError('Cédula no encontrada o cliente inactivo')
        return cedula
