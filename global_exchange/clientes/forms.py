from django import forms
from .models import Cliente

class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ['nombre', 'email', 'telefono', 'segmentacion', 'estado']
        labels = {
            'nombre': 'Nombre',
            'email': 'Correo Electrónico',
            'telefono': 'Teléfono',
            'segmentacion': 'Segmentación',
            'estado': 'Estado',
        }
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'id': 'id_nombre',
                'placeholder': 'Ingrese el nombre del cliente'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'id': 'id_email',
                'placeholder': 'Ingrese el correo electrónico'
            }),
            'telefono': forms.TextInput(attrs={
                'class': 'form-control',
                'id': 'id_telefono',
                'placeholder': 'Ingrese el número de teléfono'
            }),
            'segmentacion': forms.Select(attrs={
                'class': 'form-control',
                'id': 'id_segmentacion'
            }),
            'estado': forms.Select(attrs={
                'class': 'form-control',
                'id': 'id_estado'
            }),
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if 'class' not in field.widget.attrs:
                field.widget.attrs.update({'class': 'form-control'})