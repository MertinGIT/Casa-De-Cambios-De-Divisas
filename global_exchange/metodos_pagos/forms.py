from django import forms
from django.core.exceptions import ValidationError
from .models import MetodoPago
import unicodedata

def _normalize_text(s: str) -> str:
    if s is None:
        return ''
    # Normaliza Unicode y quita espacios en ambos extremos
    return unicodedata.normalize('NFKC', s).strip()

class MetodoPagoForm(forms.ModelForm):
    class Meta:
        model = MetodoPago
        fields = ['nombre', 'descripcion']
        labels = {
            'nombre': 'Nombre',
            'descripcion': 'Descripción',
        }
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control custom-input',
                'id': 'id_nombre',
                'placeholder': 'Ingrese el nombre',
                'maxlength': '100',
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control custom-input',
                'id': 'id_descripcion',
                'placeholder': 'Ingrese la descripción (opcional)',
                'rows': 3,
                'maxlength': '500',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['nombre'].required = True
        self.fields['descripcion'].required = False

    def clean_nombre(self):
        raw = self.cleaned_data.get('nombre', '')
        nombre = _normalize_text(raw)
        
        if not nombre:
            raise ValidationError("El nombre es obligatorio.")
        
        if len(nombre) < 3:
            raise ValidationError("El nombre debe tener al menos 3 caracteres.")
        
        if len(nombre) > 100:
            raise ValidationError("El nombre no puede exceder 100 caracteres.")

        # Validación única — case-insensitive, excluye la instancia actual
        qs = MetodoPago.objects.filter(nombre__iexact=nombre)
        if self.instance and getattr(self.instance, 'pk', None):
            qs = qs.exclude(pk=self.instance.pk)
        
        if qs.exists():
            raise ValidationError("Este nombre ya existe, por favor elige otro.")
        
        return nombre

    def clean_descripcion(self):
        descripcion = self.cleaned_data.get('descripcion', '')
        if descripcion:
            descripcion = _normalize_text(descripcion)
            if len(descripcion) > 500:
                raise ValidationError("La descripción no puede exceder 500 caracteres.")
        return descripcion or None  # Retorna None para campos vacíos