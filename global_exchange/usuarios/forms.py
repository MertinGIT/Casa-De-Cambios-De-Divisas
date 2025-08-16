from pyexpat.errors import messages
from urllib import request
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import UserChangeForm

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    ci_ruc = forms.CharField(max_length=20, required=True)

    password1 = forms.CharField(
        label="Password",
        strip=False,
        widget=forms.PasswordInput,
        help_text="Your password must contain at least 8 characters. Your password can’t be entirely numeric."
    )
    password2 = forms.CharField(
        label="Password confirmation",
        strip=False,
        widget=forms.PasswordInput,
        help_text="Enter the same password as before, for verification."
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'ci_ruc', 'password1', 'password2')

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

    class Meta:
        model = User
        fields = ('email', 'username')

    def __init__(self, *args, **kwargs):
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