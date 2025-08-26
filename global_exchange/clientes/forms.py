from django import forms
from .models import Cliente, Segmentacion

class ClienteForm(forms.ModelForm):
    segmentacion = forms.ModelChoiceField(
        queryset=Segmentacion.objects.all(),
        empty_label="Seleccione un segmento",  # obliga a elegir
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_segmentacion'})
    )

    estado = forms.CharField(
        max_length=10,
        initial='activo',
        required=False,  # no será obligatorio porque lo fijamos nosotros
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'readonly': 'readonly'
        })
    )

    class Meta:
        model = Cliente
        fields = ['nombre', 'email', 'telefono', 'segmentacion', 'estado']
        labels = {
            'nombre': 'Nombre',
            'email': 'Correo Electrónico',
            'telefono': 'Teléfono',
            'segmentacion': 'Segmentación',
            'estado': 'Estado',
            'estado': 'Estado',
        }
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ingrese el nombre'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Ingrese el correo'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ingrese teléfono'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Valor inicial fijo para estado en creación
        if not self.instance.pk:
            self.fields['estado'].initial = 'activo'

    