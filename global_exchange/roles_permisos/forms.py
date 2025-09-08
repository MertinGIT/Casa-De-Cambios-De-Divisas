from django import forms
from django.contrib.auth.models import Group, Permission
from usuarios.models import CustomUser


class RolForm(forms.ModelForm):
    """
    Formulario para la creación y edición de roles en el sistema.

    Este formulario permite definir un rol a partir del modelo
    :class:`django.contrib.auth.models.Group`, y asignarle permisos
    mediante un campo de selección múltiple.

    Attributes
    ----------
    permisos : ModelMultipleChoiceField
        Lista de permisos asociados al rol, representados en un widget
        de selección múltiple.

    Meta
    ----
    model : Group
        Modelo base utilizado para la creación del rol.
    fields : list
        Campos incluidos en el formulario: ``name`` y ``permisos``.
    widgets : dict
        Configuración de los widgets, incluyendo clases CSS y
        atributos adicionales.

    Notas
    -----
    - Se utiliza un ``ModelMultipleChoiceField`` para asignar múltiples permisos a un rol.
    - En el método :meth:`__init__` se inicializan los permisos actuales del grupo
      si el rol ya existe.
    - En el método :meth:`save` se asignan correctamente los permisos seleccionados
      al rol creado o editado.
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
            'name': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': 'Ingrese el nombre del rol'}
            ),
        }

    def __init__(self, *args, **kwargs):
        """
        Inicializa el formulario y asigna permisos iniciales si el rol ya existe.

        Parameters
        ----------
        *args : list
            Argumentos posicionales para el formulario base.
        **kwargs : dict
            Argumentos con nombre para el formulario base.
        """
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['permisos'].initial = self.instance.permissions.values_list(
                'id', flat=True
            )

    def save(self, commit=True):
        """
        Guarda el rol junto con sus permisos asignados.

        Parameters
        ----------
        commit : bool, optional
            Si es ``True`` (por defecto), se guarda inmediatamente
            el rol y se asignan sus permisos.

        Returns
        -------
        Group
            La instancia del rol (grupo) creada o modificada.
        """
        group = super().save(commit=False)
        if commit:
            group.save()
            if self.cleaned_data.get('permisos') is not None:
                group.permissions.set(self.cleaned_data['permisos'])
            self.save_m2m()
        return group
