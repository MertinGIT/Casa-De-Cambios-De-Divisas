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
User = get_user_model()
class CustomUserCreationForm(UserCreationForm):
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
        label="Password",
        strip=False,
        widget=forms.PasswordInput(attrs={'placeholder': ' '}),
        help_text="Your password must contain at least 8 characters. Your password can’t be entirely numeric."
    )
    password2 = forms.CharField(
        label="Password confirmation",
        strip=False,
        widget=forms.PasswordInput(attrs={'placeholder': ' '}),
        help_text="Enter the same password as before, for verification."
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'cedula', 'password1', 'password2')


    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            self.add_error('email', "Este email ya está registrado.")
        return email
    
    def clean_password1(self):
        password1 = self.cleaned_data.get("password1")
        try:
            validate_password(password1, self.instance)
        except ValidationError as e:
            # Filtramos los mensajes para que solo aparezcan los que queremos
            messages = [msg for msg in e.messages if "at least 8 characters" in msg or "entirely numeric" in msg]
            if messages:
               self.add_error('password1', messages)
        return password1
        
    def save(self, commit=True):
        user = super().save(commit=False)
        # Guardamos el cedula
        user.cedula = self.cleaned_data.get('cedula')
        if commit:
            user.save()
        return user


class CustomUserChangeForm(UserChangeForm):
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

    cedula = forms.CharField(
        label="cedula",
        required=True,
        max_length=20  
    )
 
    class Meta:
        model = User
        fields = ('email', 'username', 'cedula')

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)  # ahora es opcional
        super().__init__(*args, **kwargs)
        self.fields['email'].disabled = True

    def clean(self):
        cleaned_data = super().clean()
        password_actual = cleaned_data.get('password_actual')
        password_nuevo = cleaned_data.get('password_nuevo')
        password_confirmacion = cleaned_data.get('password_confirmacion')

        if password_nuevo or password_confirmacion:
            if not password_actual:
                self.add_error('password_actual', "Debes ingresar tu contraseña actual para cambiarla.")
            elif not self.instance.check_password(password_actual):
                self.add_error('password_actual', "La contraseña actual es incorrecta.")

            try:
                validate_password(password_nuevo, self.instance)
            except ValidationError as e:
                mensajes_filtrados = [
                    msg for msg in e.messages
                    if "at least 8 characters" in msg or "entirely numeric" in msg
                ]
                if mensajes_filtrados:
                    self.add_error('password_nuevo', mensajes_filtrados)

            if password_nuevo != password_confirmacion:
                self.add_error('password_confirmacion', "Las contraseñas no coinciden.")
        else:
            if not self.instance.check_password(password_actual):
                self.add_error('password_actual', "La contraseña actual no es correcta.")
            
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        password_nuevo = self.cleaned_data.get('password_nuevo')
        if password_nuevo:
            user.set_password(password_nuevo)
        if commit:
            user.save()
        return user
    

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