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
        initial='activo'
    )
    class Meta:
        model = Cliente
        fields = ['nombre', 'email', 'telefono', 'segmentacion', 'estado']
        labels = {
            'nombre': 'Nombre',
            'email': 'Correo Electrónico',
            'telefono': 'Teléfono',
            'segmentacion': 'Segmentación',
            'estado': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
        }
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ingrese el nombre'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Ingrese el correo'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ingrese teléfono'}),
            'estado': forms.Select(attrs={'class': 'form-control', 'id': 'id_estado'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # asegurar que todos los campos tengan clase form-control
        for field_name, field in self.fields.items():
            if 'class' not in field.widget.attrs:
                field.widget.attrs.update({'class': 'form-control'})
            if not self.instance.pk:
                self.fields['estado'].initial = 'activo'
        self.fields['estado'].widget.attrs.update({'readonly': 'readonly', 'class': 'form-control'})

    # Validación de nombre
    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre')
        if not nombre:
            raise forms.ValidationError("El nombre es obligatorio.")
        return nombre

    # Validación de email
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not email:
            raise forms.ValidationError("El correo es obligatorio.")
        # Django ya valida formato de email con EmailField, pero podemos reforzar
        if '@' not in email:
            raise forms.ValidationError("Ingrese un correo válido.")
        return email

    # Validación de teléfono
    def clean_telefono(self):
        telefono = self.cleaned_data.get('telefono')
        if not telefono:
            raise forms.ValidationError("El teléfono es obligatorio.")
        return telefono

    # Validación de segmentación
    def clean_segmentacion(self):
        segmentacion = self.cleaned_data.get('segmentacion')
        if not segmentacion:
            raise forms.ValidationError("Debe seleccionar un segmento.")
        return segmentacion
