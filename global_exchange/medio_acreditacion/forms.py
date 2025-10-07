# forms.py
from django import forms
from .models import TipoEntidadFinanciera, MedioAcreditacion
from clientes.models import Cliente


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
    Solo permite crear y editar instancias de `MedioAcreditacion` con los campos actuales: cliente, entidad, estado.
    """

    class Meta:
        model = MedioAcreditacion
        fields = [
            'cliente', 'entidad', 'estado'
        ]
        widgets = {
            'cliente': forms.Select(attrs={
                'class': 'form-control'
            }),
            'entidad': forms.Select(attrs={
                'class': 'form-control'
            }),
            'estado': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'cliente': 'Cliente',
            'entidad': 'Entidad Financiera',
            'estado': 'Activo',
        }

    def __init__(self, *args, **kwargs):
        cliente_id = kwargs.pop('cliente_id', None)
        super().__init__(*args, **kwargs)
        self.fields['entidad'].queryset = TipoEntidadFinanciera.objects.filter(estado=True)
        self.fields['cliente'].queryset = Cliente.objects.filter(estado='activo')
        if cliente_id:
            self.fields['cliente'].initial = cliente_id
            self.fields['cliente'].widget = forms.HiddenInput()