# forms.py
from django import forms
from .models import TipoEntidadFinanciera, MedioAcreditacion
from clientes.models import Cliente
from monedas.models import Moneda


class TipoEntidadFinancieraForm(forms.ModelForm):
    """
    Formulario para gestionar tipos de entidades financieras.

    Permite crear y editar instancias de `TipoEntidadFinanciera`.

    Métodos de limpieza personalizados:
        - `clean_nombre`: Normaliza y valida que el nombre de la entidad no se duplique.
    """
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
        """
        Limpia y valida el campo `nombre`.

        - Normaliza el texto (strip y title).
        - Verifica que no exista otra entidad financiera con el mismo nombre (case-insensitive).
        - Excluye la instancia actual si se está editando.

        :raises forms.ValidationError: Si ya existe una entidad con el mismo nombre.
        :return: Nombre normalizado.
        """
        nombre = self.cleaned_data.get('nombre')
        if nombre:
            nombre = nombre.strip().title()

            queryset = TipoEntidadFinanciera.objects.filter(
                nombre__iexact=nombre)
            if self.instance and self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)

            if queryset.exists():
                raise forms.ValidationError(
                    'Ya existe una entidad con este nombre.')

        return nombre


class MedioAcreditacionForm(forms.ModelForm):
    """
    Formulario para gestionar medios de acreditación de clientes.

    Permite crear y editar instancias de `MedioAcreditacion`.

    Inicialización personalizada:
        - Filtra entidades, clientes y monedas activas.
        - Permite preseleccionar y ocultar el cliente si se proporciona `cliente_id`.

    Métodos de limpieza personalizados:
        - `clean_numero_cuenta`: Normaliza el número de cuenta.
        - `clean_titular`: Normaliza el nombre del titular.
        - `clean`: Valida que no exista un medio de acreditación duplicado para la misma entidad y número de cuenta.
    """

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
        """
        Inicializa el formulario con filtros personalizados.

        :param cliente_id: Si se proporciona, selecciona automáticamente el cliente y oculta el campo.
        """
        cliente_id = kwargs.pop('cliente_id', None)
        super().__init__(*args, **kwargs)

        self.fields['entidad'].queryset = TipoEntidadFinanciera.objects.filter(
            estado=True)
        self.fields['cliente'].queryset = Cliente.objects.filter(
            estado='activo')
        self.fields['moneda'].queryset = Moneda.objects.filter(
            estado=True)

        if cliente_id:
            self.fields['cliente'].initial = cliente_id
            self.fields['cliente'].widget = forms.HiddenInput()

    def clean_numero_cuenta(self):
        """
        Limpia y normaliza el campo `numero_cuenta`.

        :return: Número de cuenta limpio.
        """
        numero_cuenta = self.cleaned_data.get('numero_cuenta')
        if numero_cuenta:
            numero_cuenta = numero_cuenta.strip()
        return numero_cuenta

    def clean_titular(self):
        """
        Limpia y normaliza el campo `titular`.

        :return: Nombre del titular en formato title.
        """
        titular = self.cleaned_data.get('titular')
        if titular:
            titular = titular.strip().title()
        return titular

    def clean(self):
        """
        Validación general del formulario.

        - Verifica que no exista otro medio de acreditación con la misma entidad y número de cuenta.
        - Excluye la instancia actual si se está editando.

        :raises forms.ValidationError: Si ya existe un medio de acreditación duplicado.
        :return: Diccionario de datos limpios.
        """
        cleaned_data = super().clean()
        entidad = cleaned_data.get('entidad')
        numero_cuenta = cleaned_data.get('numero_cuenta')

        if entidad and numero_cuenta:
            queryset = MedioAcreditacion.objects.filter(
                entidad=entidad,
                numero_cuenta=numero_cuenta
            )
            if self.instance and self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)

            if queryset.exists():
                raise forms.ValidationError(
                    f'Ya existe un medio de acreditación con el número {numero_cuenta} '
                    f'en {entidad.nombre}.'
                )

        return cleaned_data