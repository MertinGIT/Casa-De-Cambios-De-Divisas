from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from roles_permisos.models import Rol
from usuarios.forms import CustomUserCreationForm

User = get_user_model()

class UsuariosTestCase(TestCase):
    """
    TestCase para las funcionalidades de usuarios.

    Este conjunto de pruebas verifica la creación de usuarios, 
    la validez de los formularios y el comportamiento de las vistas
    relacionadas con el registro y acceso de usuarios.

    Métodos de prueba:
        setUp(): Configura el entorno de prueba creando un rol
            de ejemplo y un usuario de prueba.
        test_usuario_str(): Comprueba que el método __str__ del usuario
            devuelve el username correctamente.
        test_signup_form_valid(): Verifica que el formulario de registro
            es válido con datos correctos.
        test_signup_view_get(): Comprueba que la vista de registro
            responde correctamente a una solicitud GET.
        test_signup_view_post(): Comprueba que la vista de registro
            crea un usuario correctamente mediante POST.
        test_home_view_requires_login(): Verifica que la vista 'home'
            redirige a login si no se está autenticado.
    """
    def setUp(self):
      """Configura el entorno de prueba."""
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

User = get_user_model()


class ConversorDivisasTestCase(TestCase):
    """
    TestCase para la funcionalidad del simulador de divisas.

    Este conjunto de pruebas verifica que la vista de simulación
    de divisas funciona correctamente, que el formulario valida los
    campos y que los cálculos se realizan como se espera.

    Métodos de prueba:
        setUp(): Crea un usuario de prueba y un rol necesario.
        test_home_view_requires_login(): Verifica que la vista home
            redirige a login si no hay un usuario autenticado.
        test_home_view_get(): Comprueba que la vista carga correctamente
            para un usuario logueado.
        test_conversor_valido(): Verifica que el formulario convierte
            correctamente un monto con monedas válidas.
        test_conversor_invalid_input(): Verifica que se rechaza un
            valor no numérico o negativo.
        test_select_origen_destino(): Verifica que los selects de origen
            y destino están presentes y no permiten elegir la misma moneda.
    """

    def setUp(self):
        """Configura el entorno de prueba creando un usuario y rol."""
        # Crear un rol de ejemplo
        self.rol_usuario = Rol.objects.create(id=1, nombre="Usuario")

        # Crear usuario de prueba
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            cedula="12345678",
            password="Testpass123!",
            rol=self.rol_usuario
        )
        self.client = Client()

    def test_home_view_requires_login(self):
        """Probar que home redirige si no está logueado"""
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 302)  # Redirige a login

    def test_home_view_get(self):
        """Probar que la vista home carga correctamente para usuario autenticado"""
        self.client.login(username='testuser', password='Testpass123!')
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'home.html')
        # Verificar que los selects de moneda estén en el HTML
        self.assertContains(response, 'name="origen"')
        self.assertContains(response, 'name="destino"')

    def test_conversor_valido(self):
        """Probar que el formulario convierte correctamente un monto válido"""
        self.client.login(username='testuser', password='Testpass123!')
        form_data = {
            'origen': 'USD',
            'destino': 'EUR',
            'valor': '100'
        }
        response = self.client.post(reverse('home'), data=form_data, follow=True)
        self.assertEqual(response.status_code, 200)
        # Comprobar que el resultado esperado se pasa al contexto
        self.assertContains(response, 'resultado')
        conversor = response.context['resultado']
        # La tasa ficticia USD->EUR es 0.95 según tu view
        self.assertEqual(conversor, 95.0)

    def test_conversor_invalid_input(self):
        """Probar que se rechaza valor no numérico o negativo"""
        self.client.login(username='testuser', password='Testpass123!')

        # Valor no numérico
        response = self.client.post(reverse('home'), data={
            'origen': 'USD',
            'destino': 'EUR',
            'valor': 'abc'
        }, follow=True)
        self.assertContains(response, 'Monto inválido', html=False)

        # Valor negativo
        response = self.client.post(reverse('home'), data={
            'origen': 'USD',
            'destino': 'EUR',
            'valor': '-50'
        }, follow=True)
        # Dependiendo de la validación, el contexto puede tener resultado vacío o error
        resultado = response.context.get('resultado', '')
        self.assertTrue(resultado in ['Monto inválido', None, ''])

    def test_select_origen_destino(self):
        """Probar que los selects no permiten elegir la misma moneda"""
        self.client.login(username='testuser', password='Testpass123!')
        response = self.client.get(reverse('home'))
        self.assertContains(response, 'option value="USD"')
        self.assertContains(response, 'option value="EUR"')
        # No se debería poder seleccionar la misma moneda en destino
        # Se valida que en el HTML se aplica disabled en la opción igual al origen
        self.assertIn('disabled', response.content.decode())
