from django import forms
from django.contrib.auth.models import Group, Permission

class RolForm(forms.ModelForm):
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

    def save(self, commit=True):
        group = super().save(commit=False)
        if commit:
            group.save()
            # Se asegura de guardar permisos seleccionados
            self.save_m2m()
        return group
