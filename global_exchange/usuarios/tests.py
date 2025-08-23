from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from roles_permisos.models import Rol
from usuarios.forms import CustomUserCreationForm

User = get_user_model()

class UsuariosTestCase(TestCase):

    def setUp(self):
    # Crear un rol de ejemplo con id=1
      self.rol_usuario = Rol.objects.create(id=1, nombre="Usuario")
    
      # Crear un usuario de prueba
      self.user = User.objects.create_user(
          username="testuser",
          email="test@example.com",
          cedula="12345678",
          password="Testpass123!",
          rol=self.rol_usuario
      )
      self.client = Client()


    def test_usuario_str(self):
        """Probar que el __str__ de CustomUser devuelve el username"""
        self.assertEqual(str(self.user), "testuser")

    def test_signup_form_valid(self):
        """Probar que el formulario de creación de usuario es válido"""
        form_data = {
            'username': 'nuevo_user',
            'email': 'nuevo@example.com',
            'cedula': '87654321',
            'password1': 'Password123!',
            'password2': 'Password123!'
        }
        form = CustomUserCreationForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_signup_view_get(self):
        """Probar que la vista signup carga correctamente con GET"""
        response = self.client.get(reverse('signup'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registrarse.html')

    def test_signup_view_post(self):
        """Probar crear usuario mediante POST en signup"""
        form_data = {
            'username': 'usuario_post',
            'email': 'usuario_post@example.com',
            'cedula': '99999999',
            'password1': 'Password123!',
            'password2': 'Password123!'
        }
        response = self.client.post(reverse('signup'), data=form_data)
        # La vista normalmente devuelve render, podemos comprobar que se creó el usuario
        self.assertTrue(User.objects.filter(username='usuario_post').exists())

    def test_home_view_requires_login(self):
        """Probar que home redirige si no está logueado"""
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 302)  # Redirige a login

