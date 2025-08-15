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

    def clean_password1(self):
        password1 = self.cleaned_data.get("password1")
        try:
            validate_password(password1, self.instance)
        except ValidationError as e:
            # Filtramos los mensajes para que solo aparezcan los que queremos
            messages = [msg for msg in e.messages if "at least 8 characters" in msg or "entirely numeric" in msg]
            if messages:
                raise ValidationError(messages)
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
        required=False
    )
    password_confirmacion = forms.CharField(
        label="Confirmación de contraseña",
        widget=forms.PasswordInput,
        required=False
    )

    class Meta:
        model = User
        fields = ['email', 'username']  # Solo los campos reales del modelo

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].disabled = True  # Hacer email de solo lectura