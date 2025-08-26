from django import forms
from django.contrib.auth.models import Group, Permission


class RolForm(forms.ModelForm):
    """
    Formulario para la creación y edición de roles en el sistema.

    Campos:
        - ``nombre`` (CharField): Nombre del rol.  
        - ``descripcion`` (TextField): Descripción detallada del rol.  
        - ``permisos`` (ModelMultipleChoiceField): Lista de permisos asociados al rol, 
          representados como checkboxes.

    Widgets:
        - ``nombre``: Campo de texto con estilo Bootstrap (``form-control``).  
        - ``descripcion``: Área de texto con estilo Bootstrap (``form-control``).  
        - ``permisos``: Checkboxes múltiples para la selección de permisos.  

    Notas:
        - Se utiliza un ``ModelMultipleChoiceField`` con widget ``CheckboxSelectMultiple`` 
          para asignar múltiples permisos a un rol.  
        - En el método ``__init__`` se asegura que todos los campos tengan la clase CSS 
          adecuada (``form-control`` o ``permisos-checkbox``).
    """

    permisos = forms.ModelMultipleChoiceField(
        queryset=Permission.objects.all(),
        widget=forms.SelectMultiple(attrs={'size': 15}),  # tamaño select
        required=False,
        label="Permisos"
    )

    class Meta:
        model = Group
        fields = ['name', 'permisos']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ingrese el nombre del rol'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['permisos'].initial = self.instance.permissions.values_list(
                'id', flat=True)

    def save(self, commit=True):
        group = super().save(commit=False)
        if commit:
            group.save()
            # Asignar los permisos seleccionados correctamente
            if self.cleaned_data.get('permisos') is not None:
                group.permissions.set(self.cleaned_data['permisos'])
            self.save_m2m()
        return group
