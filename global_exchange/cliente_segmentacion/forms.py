from django import forms
from clientes.models import Segmentacion

class SegmentacionForm(forms.ModelForm):
    estado = forms.CharField(
        max_length=10,
        initial='activo',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'readonly': 'readonly',
            'value': 'activo'
        })
    )
    class Meta:
        model = Segmentacion
        fields = ['nombre', 'descripcion', 'descuento', 'estado']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'custom-input', 'placeholder': 'Nombre del tipo de cliente'}),
            'descripcion': forms.TextInput(attrs={'class': 'custom-input', 'placeholder': 'Descripción del tipo de cliente', 'rows': 3}),
            'descuento': forms.NumberInput(attrs={'class': 'custom-input', 'placeholder': 'Descuento en porcentaje'}),
            'estado': forms.Select(attrs={'class': 'custom-input'}),
        }
        labels = {
            'nombre': 'Tipo de cliente',
            'descripcion': 'Descripción',
            'descuento': 'Descuento (%)',
            'estado': 'Estado',
        }
        help_texts = { 
            'descuento': 'Ingrese el porcentaje de descuento asociado a este tipo de cliente.',
            'estado': 'Seleccione el estado de la segmentación (activo/inactivo).',
        }