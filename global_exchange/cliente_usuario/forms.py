# clientes/forms.py
from django import forms
from django.contrib.admin.widgets import FilteredSelectMultiple
from clientes.models import Cliente
from usuarios.models import CustomUser
from .models import Usuario_Cliente

class ClienteUsuariosForm(forms.ModelForm):
    """
    Formulario para asignar usuarios a un cliente.
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
        super().__init__(*args, **kwargs)
        # Precargar usuarios asignados si el cliente ya existe
        if self.instance and self.instance.pk:
            self.fields['usuarios'].initial = self.instance.usuarios.all()

    def save(self, commit=True):
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
