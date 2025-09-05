from django import forms
from .models import Cliente, Segmentacion

class ClienteForm(forms.ModelForm):
    """
    Formulario para crear y editar instancias del modelo Cliente.

    Campos:
        - nombre: Nombre del cliente (mínimo 3 caracteres, obligatorio).
        - email: Correo electrónico único del cliente (obligatorio).
        - telefono: Teléfono del cliente (opcional).
        - segmentacion: Segmentación asignada al cliente (obligatorio, solo activos).
        - estado: Estado del cliente ('activo' por defecto), solo lectura en el formulario.
    """

    segmentacion = forms.ModelChoiceField(
        queryset=Segmentacion.objects.filter(estado='activo'),
        empty_label="Seleccione un segmento",
        required=True,
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
        """
        Inicializa el formulario y configura campos obligatorios y valores por defecto.
        """
        super().__init__(*args, **kwargs)
        # Valor inicial fijo para estado en creación
        if not self.instance.pk:
            self.fields['estado'].initial = 'activo'
        
        # Campos obligatorios más explícitos
        self.fields['nombre'].required = True
        self.fields['email'].required = True
        self.fields['segmentacion'].required = True

    def clean_nombre(self):
        """
        Valida el campo 'nombre'.

        Reglas:
            - Obligatorio
            - Mínimo 3 caracteres

        Raises:
            forms.ValidationError: Si el nombre no cumple las reglas.

        Returns:
            str: Nombre limpio (sin espacios al inicio o final).
        """
        nombre = self.cleaned_data.get('nombre')
        if not nombre:
            raise forms.ValidationError("Este campo es obligatorio.")
        if len(nombre.strip()) < 3:
            raise forms.ValidationError("El nombre debe tener al menos 3 caracteres.")
        return nombre.strip()

    def clean_email(self):
        """
        Valida el campo 'email'.

        Reglas:
            - Obligatorio
            - Debe ser único (excluyendo la instancia actual en edición)

        Raises:
            forms.ValidationError: Si el email está vacío o ya existe.

        Returns:
            str: Email limpio.
        """
        email = self.cleaned_data.get('email')
        if not email:
            raise forms.ValidationError("Este campo es obligatorio.")
        
        qs = Cliente.objects.filter(email=email)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        
        if qs.exists():
            raise forms.ValidationError("Este correo ya está registrado.")
        return email

    def clean_segmentacion(self):
        """
        Valida el campo 'segmentacion'.

        Reglas:
            - Obligatorio
            - Debe ser una segmentación activa

        Raises:
            forms.ValidationError: Si no se selecciona un segmento.

        Returns:
            Segmentacion: Instancia seleccionada.
        """
        segmentacion = self.cleaned_data.get('segmentacion')
        if not segmentacion:
            raise forms.ValidationError("Debe seleccionar un segmento.")
        return segmentacion
