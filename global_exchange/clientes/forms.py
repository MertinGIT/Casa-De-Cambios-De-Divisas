from django import forms
from .models import Cliente, Segmentacion

class ClienteForm(forms.ModelForm):
    segmentacion = forms.ModelChoiceField(
        queryset=Segmentacion.objects.all(),
        empty_label="Seleccione un segmento",
        required=True,  # Hacerlo obligatorio
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_segmentacion'})
    )
    
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
                'placeholder': 'Ingrese el nombre',
                'required': True
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Ingrese el correo',
                'required': True
            }),
            'telefono': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Ingrese teléfono'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Valor inicial fijo para estado en creación
        if not self.instance.pk:
            self.fields['estado'].initial = 'activo'
            
        # Hacer campos obligatorios más explícitos
        self.fields['nombre'].required = True
        self.fields['email'].required = True
        self.fields['segmentacion'].required = True

    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre')
        if not nombre:
            raise forms.ValidationError("Este campo es obligatorio.")
        if len(nombre.strip()) < 3:
            raise forms.ValidationError("El nombre debe tener al menos 3 caracteres.")
        return nombre.strip()

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not email:
            raise forms.ValidationError("Este campo es obligatorio.")
        
        # Verificar si ya existe (excluyendo la instancia actual en edición)
        qs = Cliente.objects.filter(email=email)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        
        if qs.exists():
            raise forms.ValidationError("Este correo ya está registrado.")
        return email

    def clean_segmentacion(self):
        segmentacion = self.cleaned_data.get('segmentacion')
        if not segmentacion:
            raise forms.ValidationError("Debe seleccionar un segmento.")
        return segmentacion