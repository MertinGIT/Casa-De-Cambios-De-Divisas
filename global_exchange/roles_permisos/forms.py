from django import forms
from .models import Rol, Permiso

class RolForm(forms.ModelForm):
    permisos = forms.ModelMultipleChoiceField(
        queryset=Permiso.objects.all(),
        widget=forms.CheckboxSelectMultiple(),
        required=False,
        label="Permisos"
    )

    class Meta:
        model = Rol
        fields = ['nombre', 'descripcion', 'permisos']
        labels = {
            'nombre': 'Nombre',
            'descripcion': 'Descripción',
        }
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'id': 'id_nombre',
                'placeholder': 'Ingrese el nombre del rol'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control', 
                'id': 'id_descripcion',
                'rows': 3,
                'placeholder': 'Ingrese la descripción del rol'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Agregar clases CSS y configuraciones adicionales
        for field_name, field in self.fields.items():
            if field_name == 'permisos':
                # Para los checkboxes de permisos, mantener el widget especial
                field.widget.attrs.update({
                    'class': 'permisos-checkbox'
                })
            else:
                # Para otros campos, asegurar que tengan la clase form-control
                if 'class' not in field.widget.attrs:
                    field.widget.attrs.update({'class': 'form-control'})