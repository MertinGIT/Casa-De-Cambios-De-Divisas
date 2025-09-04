from django import forms
from .models import Rol, Permiso

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
        """
        Inicializa el formulario aplicando clases CSS personalizadas 
        a los widgets de cada campo.
        
        - Para el campo ``permisos``: aplica la clase ``permisos-checkbox``.  
        - Para el resto: asegura que tengan la clase ``form-control``.
        """
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