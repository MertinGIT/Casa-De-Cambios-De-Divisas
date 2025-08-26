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

    # ---------- VALIDACIONES PERSONALIZADAS ----------

    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre')
        if not nombre:
            raise forms.ValidationError("El nombre es obligatorio.")
        if len(nombre) < 3:
            raise forms.ValidationError("El nombre debe tener al menos 3 caracteres.")
        return nombre

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not email:
            raise forms.ValidationError("El correo es obligatorio.")
        if '@' not in email:
            raise forms.ValidationError("Ingrese un correo válido.")
        # Evitar duplicados (excepto si es edición del mismo cliente)
        if Cliente.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("Ya existe un cliente con este correo.")
        return email

    def clean_telefono(self):
        telefono = self.cleaned_data.get('telefono')
        if not telefono:
            raise forms.ValidationError("El teléfono es obligatorio.")
        if not telefono.isdigit():
            raise forms.ValidationError("El teléfono debe contener solo números.")
        if len(telefono) < 7:
            raise forms.ValidationError("El teléfono debe tener al menos 7 dígitos.")
        return telefono

    def clean_segmentacion(self):
        segmentacion = self.cleaned_data.get('segmentacion')
        if not segmentacion:
            raise forms.ValidationError("Debe seleccionar un segmento.")
        return segmentacion

    def clean_estado(self):
        """Forzar siempre que el estado sea 'activo' al crear."""
        estado = self.cleaned_data.get('estado')
        if not estado:
            return 'activo'
        return estado
