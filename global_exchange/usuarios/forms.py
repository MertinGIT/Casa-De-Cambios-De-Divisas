from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

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
