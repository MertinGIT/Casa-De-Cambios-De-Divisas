from django import forms
from django.contrib.admin.widgets import FilteredSelectMultiple
from clientes.models import Cliente
from usuarios.models import CustomUser
from .models import Usuario_Cliente

class ClienteUsuariosForm(forms.ModelForm):
    """
    Formulario para asignar usuarios a un cliente específico.

    Campos
    ------
    usuarios : ModelMultipleChoiceField
        Lista de usuarios disponibles para asignar al cliente.  
        Se utiliza el widget ``FilteredSelectMultiple`` para selección múltiple con estilo de admin de Django.

    Métodos
    -------
    __init__(*args, **kwargs)
        Inicializa el formulario y precarga los usuarios asignados si el cliente ya existe.

    save(commit=True)
        Guarda los cambios del cliente y actualiza la tabla intermedia ``Usuario_Cliente``:
            - Elimina las relaciones anteriores del cliente.
            - Crea nuevas relaciones para los usuarios seleccionados.

    Notas
    -----
    - El formulario está vinculado al modelo ``Cliente`` y solo expone el campo ``usuarios``.
    - Las relaciones intermedias se manejan de forma automática al guardar el formulario.
    """
    
    usuarios = forms.ModelMultipleChoiceField(
        queryset=CustomUser.objects.all(),
        widget=FilteredSelectMultiple("Usuarios asignados", is_stacked=False),
        required=False,
        label="Usuarios asignados"
    )

    class Meta:
        model = Cliente
        fields = ['usuarios']

    def __init__(self, *args, **kwargs):
        """
        Inicializa el formulario y precarga los usuarios asignados si el cliente ya existe.

        :param args: Argumentos posicionales para el constructor del formulario.
        :param kwargs: Argumentos de palabra clave para el constructor del formulario.
        """
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['usuarios'].initial = self.instance.usuarios.all()

    def save(self, commit=True):
        """
        Guarda los cambios del cliente y actualiza las relaciones intermedias con los usuarios.

        :param commit: Indica si se debe guardar inmediatamente en la base de datos.
        :type commit: bool
        :return: Instancia del cliente guardada.
        :rtype: Cliente
        """
        cliente = super().save(commit=False)
        if commit:
            cliente.save()

        # Actualizar relaciones Usuario_Cliente
        if 'usuarios' in self.cleaned_data:
            usuarios_seleccionados = self.cleaned_data['usuarios']

            # eliminar relaciones anteriores
            Usuario_Cliente.objects.filter(id_cliente=cliente).delete()

            # crear nuevas relaciones
            Usuario_Cliente.objects.bulk_create([
                Usuario_Cliente(id_usuario=usuario, id_cliente=cliente)
                for usuario in usuarios_seleccionados
            ])

        return cliente
