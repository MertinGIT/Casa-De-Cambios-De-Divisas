# forms.py
from django import forms
from .models import TipoEntidadFinanciera, MedioAcreditacion
from clientes.models import Cliente
from monedas.models import Moneda


class TipoEntidadFinancieraForm(forms.ModelForm):
    """Formulario para gestionar tipos de entidades financieras"""

    class Meta:
        model = TipoEntidadFinanciera
        fields = ['nombre', 'tipo']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Banco Itaú Paraguay',
                'maxlength': 100
            }),
            'tipo': forms.Select(attrs={
                'class': 'form-control'
            }),
        }
        labels = {
            'nombre': 'Nombre de la Entidad',
            'tipo': 'Tipo de Entidad',
        }
        help_texts = {
            'nombre': 'Nombre completo de la entidad financiera',
            'tipo': 'Seleccione el tipo de entidad financiera',
        }

    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre')
        if nombre:
            nombre = nombre.strip().title()

            # Verificar si ya existe (excluyendo la instancia actual si estamos editando)
            queryset = TipoEntidadFinanciera.objects.filter(
                nombre__iexact=nombre)
            if self.instance and self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)

            if queryset.exists():
                raise forms.ValidationError(
                    'Ya existe una entidad con este nombre.')

        return nombre


class MedioAcreditacionForm(forms.ModelForm):
    """Formulario para gestionar medios de acreditación"""

    class Meta:
        model = MedioAcreditacion
        fields = [
            'cliente', 'entidad', 'numero_cuenta', 'tipo_cuenta',
            'titular', 'documento_titular', 'moneda'
        ]
        widgets = {
            'cliente': forms.Select(attrs={
                'class': 'form-control'
            }),
            'entidad': forms.Select(attrs={
                'class': 'form-control'
            }),
            'numero_cuenta': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: 1234567890 o 0981123456',
                'maxlength': 50
            }),
            'tipo_cuenta': forms.Select(attrs={
                'class': 'form-control'
            }),
            'titular': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre completo del titular',
                'maxlength': 200
            }),
            'documento_titular': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'CI/RUC del titular',
                'maxlength': 20
            }),
            'moneda': forms.Select(attrs={
                'class': 'form-control'
            }),
        }
        labels = {
            'cliente': 'Cliente',
            'entidad': 'Entidad Financiera',
            'numero_cuenta': 'Número de Cuenta/Teléfono',
            'tipo_cuenta': 'Tipo de Cuenta',
            'titular': 'Titular de la Cuenta',
            'documento_titular': 'Documento del Titular',
            'moneda': 'Moneda',
        }

    def __init__(self, *args, **kwargs):
        cliente_id = kwargs.pop('cliente_id', None)
        super().__init__(*args, **kwargs)

        # Filtrar solo entidades activas
        self.fields['entidad'].queryset = TipoEntidadFinanciera.objects.filter(
            estado=True)

        # Filtrar solo clientes activos
        self.fields['cliente'].queryset = Cliente.objects.filter(
            estado='activo')
        
        self.fields['moneda'].queryset = Moneda.objects.filter(
            estado=True)

        # Si se proporciona un cliente_id, preseleccionarlo y ocultarlo
        if cliente_id:
            self.fields['cliente'].initial = cliente_id
            self.fields['cliente'].widget = forms.HiddenInput()

    def clean_numero_cuenta(self):
        numero_cuenta = self.cleaned_data.get('numero_cuenta')
        if numero_cuenta:
            numero_cuenta = numero_cuenta.strip()
        return numero_cuenta

    def clean_titular(self):
        titular = self.cleaned_data.get('titular')
        if titular:
            titular = titular.strip().title()
        return titular

    def clean(self):
        cleaned_data = super().clean()
        entidad = cleaned_data.get('entidad')
        numero_cuenta = cleaned_data.get('numero_cuenta')

        if entidad and numero_cuenta:
            # Verificar que no exista otro medio con la misma entidad y número de cuenta
            queryset = MedioAcreditacion.objects.filter(
                entidad=entidad,
                numero_cuenta=numero_cuenta
            )

            # Si estamos editando, excluir la instancia actual
            if self.instance and self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)

            if queryset.exists():
                raise forms.ValidationError(
                    f'Ya existe un medio de acreditación con el número {numero_cuenta} '
                    f'en {entidad.nombre}.'
                )

        return cleaned_data
