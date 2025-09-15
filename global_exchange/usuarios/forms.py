from pyexpat.errors import messages
from urllib import request
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import UserChangeForm
from django.contrib.auth import password_validation
from django.core.exceptions import ValidationError
from django.contrib.auth import authenticate
from django.contrib.auth.models import Group, Permission
from .models import CustomUser
User = get_user_model()

class CustomUserCreationForm(UserCreationForm):
    """
    Formulario personalizado para la creación de usuarios.

    Extiende de :class:`django.contrib.auth.forms.UserCreationForm` y agrega
    validaciones extra como la unicidad del email y mensajes personalizados
    para la contraseña.

    Campos:
        - **username** (*CharField*): Nombre de usuario obligatorio.
        - **email** (*EmailField*): Correo electrónico único y obligatorio.
        - **cedula** (*CharField*): Documento de identidad obligatorio.
        - **password1** (*CharField*): Contraseña.
        - **password2** (*CharField*): Confirmación de contraseña.

    Métodos:
        - **clean_email()**: Verifica que el email no esté registrado.
        - **clean_password1()**: Valida la contraseña según las políticas de Django y traduce los mensajes de error al español.
        - **save(commit=True)**: Guarda el usuario incluyendo la cédula.
    """
    username = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': ' '})
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'placeholder': ' '})
    )
    cedula = forms.CharField(
        max_length=20,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': ' '})
    )
    password1 = forms.CharField(
        label="Contraseña",
        strip=False,
        widget=forms.PasswordInput(attrs={'placeholder': ' '})
    )
    password2 = forms.CharField(
        label="Repetir contraseña",
        strip=False,
        widget=forms.PasswordInput(attrs={'placeholder': ' '})
    )

    def clean_email(self):
        """
        Verifica si el email ingresado ya existe en la base de datos.

        :raises ValidationError: Si el email ya está registrado.
        :return: Email validado.
        :rtype: str
        """
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            self.add_error('email', "Este email ya está registrado.")
        return email
    
    
    def _validate_password_rules(self, password, field_name):
        try:
            validate_password(password, self.instance)
        except ValidationError as e:
            mensajes_traducidos = []
            for msg in e.messages:
                if "This password is too short" in msg:
                    mensajes_traducidos.append("Debe contener al menos 8 caracteres.")
                elif "This password is too common" in msg:
                    mensajes_traducidos.append("La contraseña es demasiado común.")
                elif "This password is entirely numeric" in msg:
                    mensajes_traducidos.append("La contraseña no puede ser solo numérica.")
                else:
                    mensajes_traducidos.append(msg)  
            self.add_error(field_name, mensajes_traducidos)

    def clean_password1(self):
        password1 = self.cleaned_data.get("password1")
        self._validate_password_rules(password1, "password1")
        return password1


    def save(self, commit=True):
        """
        Guarda el usuario en la base de datos.

        :param commit: Si es True, guarda el usuario inmediatamente.
        :type commit: bool
        :return: Instancia del usuario creado.
        :rtype: User
        """
        user = super().save(commit=False)
        # Guardamos el cedula
        user.cedula = self.cleaned_data.get('cedula')
        if commit:
            user.save()
        return user

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].error_messages['required'] = 'Debes ingresar un nombre de usuario.'
        self.fields['email'].error_messages['required'] = 'Debes ingresar un email.'
        self.fields['cedula'].error_messages['required'] = 'Debes ingresar la cédula.'
        self.fields['password1'].error_messages['required'] = 'Debes ingresar una contraseña.'
        self.fields['password2'].error_messages['required'] = 'Debes repetir la contraseña.'

    class Meta:
            model = User
            fields = ('username', 'email', 'cedula', 'password1', 'password2')

    

class CustomUserChangeForm(UserChangeForm):
    """
    Formulario personalizado para la actualización de datos de usuario.

    Extiende de :class:`django.contrib.auth.forms.UserChangeForm` y permite
    cambiar datos básicos del usuario y su contraseña.

    Campos adicionales:
        - **password_actual** (*CharField*): Contraseña actual para validación.
        - **password_nuevo** (*CharField*): Nueva contraseña.
        - **password_confirmacion** (*CharField*): Confirmación de la nueva contraseña.
        - **cedula** (*CharField*): Documento de identidad obligatorio.
        - **email** (*CharField*): Correo electrónico, solo lectura.

    **Métodos:**
        - **clean()**: Verifica que las contraseñas sean correctas y coincidan.
        - **save(commit=True)**: Actualiza la información del usuario y cambia la contraseña si fue ingresada.
    """
    password_actual = forms.CharField(
        label="Contraseña actual",
        widget=forms.PasswordInput,
        required=False
    )
    password_nuevo = forms.CharField(
        label="Contraseña nueva",
        widget=forms.PasswordInput,
        required=False
    )
    password_confirmacion = forms.CharField(
        label="Repetir contraseña nueva",
        widget=forms.PasswordInput,
        required=False
    )

    cedula = forms.CharField(
        label="Cédula",
        required=True,
        max_length=20,
        error_messages={
            'required': 'La cédula es obligatoria.',
            'max_length': 'La cédula no puede superar los 20 caracteres.'
        }
    )

    email = forms.CharField(
        label="email",
        required=True,
        max_length=40  
    )
    class Meta:
        model = User
        fields = ('email', 'username', 'cedula')

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)  # ahora es opcional
        super().__init__(*args, **kwargs)
        self.fields['email'].disabled = True

    def _validate_password_rules(self, password, field_name):
        """
        Valida la contraseña nueva contra las reglas de Django y
        traduce los mensajes al español.
        """
        try:
            validate_password(password, self.instance)
        except ValidationError as e:
            mensajes_traducidos = []
            for msg in e.messages:
                if "This password is too short" in msg:
                    mensajes_traducidos.append("Debe contener al menos 8 caracteres.")
                elif "This password is too common" in msg:
                    mensajes_traducidos.append("La contraseña es demasiado común.")
                elif "This password is entirely numeric" in msg:
                    mensajes_traducidos.append("La contraseña no puede ser solo numérica.")
                else:
                    mensajes_traducidos.append(msg)
            self.add_error(field_name, mensajes_traducidos)

    def clean(self):
        """
        Realiza las validaciones personalizadas del formulario.

        - Comprueba que la contraseña actual sea correcta.
        - Valida la seguridad de la nueva contraseña.
        - Verifica que la nueva contraseña y su confirmación coincidan.

        :raises ValidationError: Si alguna validación falla.
        :return: Datos validados del formulario.
        :rtype: dict
        """
        cleaned_data = super().clean()
        password_actual = cleaned_data.get('password_actual')
        password_nuevo = cleaned_data.get('password_nuevo')
        password_confirmacion = cleaned_data.get('password_confirmacion')
        cedula = cleaned_data.get('cedula')

        if password_nuevo or password_confirmacion:
            if not password_actual:
                self.add_error('password_actual', "Debes ingresar tu contraseña actual para cambiarla.")
            elif not self.instance.check_password(password_actual):
                self.add_error('password_actual', "La contraseña actual es incorrecta.")

            # validar reglas de seguridad con mensajes traducidos
            if password_nuevo:
                # 🚨 verificar si es igual a la actual
                if self.instance.check_password(password_nuevo):
                    self.add_error('password_nuevo', "La nueva contraseña no puede ser igual a la contraseña actual.")
                else:
                    self._validate_password_rules(password_nuevo, 'password_nuevo')

            if password_nuevo != password_confirmacion:
                self.add_error('password_confirmacion', "Las contraseñas no coinciden.")
        else:
            # Si no se quiere cambiar contraseña, igual debe ingresar la actual
            if not self.instance.check_password(password_actual):
                self.add_error('password_actual', "Para realizar cambios debe ingresar la contraseña actual.")

        return cleaned_data

    def save(self, commit=True):
        """
        Guarda los cambios del usuario en la base de datos.1

        :param commit: Si es True, guarda el usuario inmediatamente.
        :type commit: bool
        :return: Instancia del usuario actualizado.
        :rtype: User
        """
        user = super().save(commit=False)
        password_nuevo = self.cleaned_data.get('password_nuevo')
        if password_nuevo:
            user.set_password(password_nuevo)
        if commit:
            user.save()
        return user


class UserRolePermissionForm(forms.ModelForm):
    # CAMBIAR: roles → groups
    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(),
        required=False,
        widget=forms.SelectMultiple(attrs={"class": "form-control"})
    )
    # CAMBIAR: user_permisos → user_permissions
    user_permissions = forms.ModelMultipleChoiceField(
        queryset=Permission.objects.all(),
        required=False,
        widget=forms.SelectMultiple(attrs={"class": "form-control"})
    )

    class Meta:
        model = CustomUser
        fields = ["username", "groups", "user_permissions"]  # También cambiar aquí
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Si estamos editando un usuario existente, pre-cargar los datos
        if self.instance and self.instance.pk:
            self.fields['groups'].initial = self.instance.groups.all()
            self.fields['user_permissions'].initial = self.instance.user_permissions.all()


"""
class CustomUserChangeForm(forms.Form):
    username = forms.CharField(label="Usuario", max_length=150, required=True)
    email = forms.EmailField(label="Correo", required=True, disabled=True)
    ci_ruc = forms.CharField(label="Cédula / RUC", max_length=20, required=True)

    password_actual = forms.CharField(
        label="Contraseña actual",
        widget=forms.PasswordInput,
        required=False
    )
    password_nuevo = forms.CharField(
        label="Contraseña nueva",
        widget=forms.PasswordInput,
        required=False,
        help_text="Debe tener al menos 8 caracteres y no puede ser completamente numérica."
    )
    password_confirmacion = forms.CharField(
        label="Confirmación de contraseña",
        widget=forms.PasswordInput,
        required=False
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')  # Pasar el usuario al instanciar el form
        super().__init__(*args, **kwargs)
        # Inicializamos valores
        self.fields['username'].initial = self.user.username
        self.fields['email'].initial = self.user.email
        self.fields['ci_ruc'].initial = getattr(self.user, 'ci_ruc', '')

    def clean(self):
        cleaned_data = super().clean()
        password_actual = cleaned_data.get('password_actual')
        password_nuevo = cleaned_data.get('password_nuevo')
        password_confirmacion = cleaned_data.get('password_confirmacion')

        if password_nuevo or password_confirmacion:
            if not password_actual:
                self.add_error('password_actual', "Debes ingresar tu contraseña actual para cambiarla.")
            elif not self.user.check_password(password_actual):
                self.add_error('password_actual', "La contraseña actual es incorrecta.")

            try:
                password_validation.validate_password(password_nuevo, self.user)
            except ValidationError as e:
                mensajes_filtrados = [
                    msg for msg in e.messages
                    if "at least 8 characters" in msg or "entirely numeric" in msg
                ]
                if mensajes_filtrados:
                    self.add_error('password_nuevo', mensajes_filtrados)

            if password_nuevo != password_confirmacion:
                self.add_error('password_confirmacion', "Las contraseñas no coinciden.")

        elif password_actual and not self.user.check_password(password_actual):
            self.add_error('password_actual', "La contraseña actual no es correcta.")

        return cleaned_data

    def save(self):
        ""Guarda los cambios del usuario""
        self.user.username = self.cleaned_data['username']
        ci_ruc = self.cleaned_data['ci_ruc']
        # Guardamos ci_ruc en el usuario si existe el campo
        if hasattr(self.user, 'ci_ruc'):
            self.user.ci_ruc = ci_ruc
        password_nuevo = self.cleaned_data.get('password_nuevo')
        if password_nuevo:
            self.user.set_password(password_nuevo)
        self.user.save()
        return self.user
"""