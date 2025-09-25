from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from usuarios.forms import CustomUserCreationForm
from monedas.models import Moneda
from cotizaciones.models import TasaDeCambio
from datetime import datetime
from django.utils import timezone

User = get_user_model()

class UsuariosViewsTest(TestCase):
    def setUp(self):
        """Configura roles, usuarios, monedas, tasas y cliente de pruebas"""
        self.client = Client()

        # Crear roles (sin duplicados)
        self.rol_usuario, _ = Group.objects.get_or_create(name="Usuario")
        self.rol_admin, _ = Group.objects.get_or_create(name="ADMIN")

        # Crear usuario normal
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            cedula="12345678",
            password="Testpass123!"
        )
        self.user.groups.add(self.rol_usuario)

        # Crear superadmin
        self.superadmin = User.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="Admin123!",
            cedula="00001"
        )
        self.superadmin.groups.add(self.rol_admin)

        # Crear monedas
        self.mxn = Moneda.objects.create(nombre="Peso Mexicano", abreviacion="MXN", estado=True)
        self.usd = Moneda.objects.create(nombre="Dólar", abreviacion="USD", estado=True)

        # Crear tasa de cambio reciente
        hoy = datetime.today()
        aware_dt = timezone.make_aware(hoy)
        TasaDeCambio.objects.create(
            moneda_origen=self.usd,
            moneda_destino=self.mxn,
            monto_compra=5000,
            monto_venta=5050,
            vigencia=aware_dt,
            estado=True
        )

    # ======================= SIGNUP =======================
    def test_signup_view_get(self):
        url = reverse("signup")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "registrarse.html")

    def test_signup_view_post_crea_usuario(self):
        url = reverse("signup")
        data = {
            "username": "nuevo_user",
            "email": "nuevo@example.com",
            "cedula": "87654321",
            "password1": "Password123!",
            "password2": "Password123!"
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(User.objects.filter(username="nuevo_user").exists())
        self.assertFalse(User.objects.get(username="nuevo_user").is_active)

    # ======================= SIGNIN =======================
    def test_signin_view_get(self):
        url = reverse("login")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "login.html")

    def test_signin_view_post_usuario_valido(self):
        url = reverse("login")
        response = self.client.post(url, {"username": "testuser", "password": "Testpass123!"})
        self.assertRedirects(response, reverse("home"))

    def test_signin_view_post_superadmin_valido(self):
        url = reverse("login")
        response = self.client.post(url, {"username": "admin", "password": "Admin123!"})
        self.assertRedirects(response, reverse("admin_dashboard"))

    def test_signin_view_post_invalido(self):
        url = reverse("login")
        response = self.client.post(url, {"username": "wrong", "password": "wrong"})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "login.html")
        self.assertContains(response, "incorrectos")

    # ======================= HOME =======================
    def test_home_view_requiere_login(self):
        url = reverse("home")
        response = self.client.get(url)
        self.assertRedirects(response, reverse("login"))

    def test_home_view_usuario_normal(self):
        self.client.login(username="testuser", password="Testpass123!")
        url = reverse("home")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "home.html")

    def test_home_view_superadmin_redirect(self):
        self.client.login(username="admin", password="Admin123!")
        url = reverse("home")
        response = self.client.get(url)
        self.assertRedirects(response, reverse("admin_dashboard"))

    # ======================= SIGNOUT =======================
    def test_signout_cierra_sesion(self):
        self.client.login(username="testuser", password="Testpass123!")
        url = reverse("signout")
        response = self.client.get(url)
        self.assertRedirects(response, reverse("pagina_aterrizaje"))

    # ======================= SIMULACION =======================
    def test_post_venta_simulacion(self):
        """Simula venta de PYG a MXN"""
        self.client.login(username="testuser", password="Testpass123!")
        url = reverse("home")
        data = {
            "valor": "10000",
            "operacion": "venta",
            "segmento": "VIP",
            "origen": "PYG",
            "destino": "MXN"
        }
        response = self.client.post(url, data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertIn("resultado", json_data)
        self.assertIn("ganancia_total", json_data)
        self.assertGreater(json_data["resultado"], 0)
        self.assertGreaterEqual(json_data["ganancia_total"], 0)

    def test_post_compra_simulacion(self):
        """Simula compra de MXN a PYG"""
        self.client.login(username="testuser", password="Testpass123!")
        url = reverse("home")
        data = {
            "valor": "100",
            "operacion": "compra",
            "segmento": "Minorista",
            "origen": "MXN",
            "destino": "PYG"
        }
        response = self.client.post(url, data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertIn("resultado", json_data)
        self.assertIn("ganancia_total", json_data)
        self.assertGreater(json_data["resultado"], 0)
        self.assertGreaterEqual(json_data["ganancia_total"], 0)
