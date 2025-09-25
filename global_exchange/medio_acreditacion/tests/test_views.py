from django.test import TestCase
from django.urls import reverse
from clientes.models import Cliente
from medio_acreditacion.models import MedioAcreditacion, TipoEntidadFinanciera
from monedas.models import Moneda
from cliente_segmentacion.models import Segmentacion
from django.contrib.auth import get_user_model

class ClienteCreateViewTest(TestCase):
    def setUp(self):
        self.url = reverse("clientes-agregar")
        self.segmentacion = Segmentacion.objects.create(nombre="Segmento Test")
        self.entidad = TipoEntidadFinanciera.objects.create(nombre="Banco Test", tipo="B", estado=True)
        self.moneda = Moneda.objects.create(nombre="Guaraní", abreviacion="PYG", estado=True)
        self.valid_cliente_data = {
            "nombre": "Cliente Test",
            "email": "cliente@test.com",
            "telefono": "123456789",
            "segmentacion": self.segmentacion.id,
        }
        self.valid_medio_data = {
            "entidad": self.entidad.id,
            "numero_cuenta": "12345678",
            "tipo_cuenta": "CA",
            "titular": "Cliente Test",
            "documento_titular": "1234567",
            "moneda": self.moneda.id,
        }
        # Crear y loguear usuario
        User = get_user_model()
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.client.login(username="testuser", password="testpass")

    def test_crear_cliente_y_medio_exitoso(self):
        post_data = {**self.valid_cliente_data, **self.valid_medio_data}
        response = self.client.post(self.url, post_data)
        self.assertRedirects(response, reverse("clientes"))
        self.assertTrue(Cliente.objects.filter(email="cliente@test.com").exists())
        cliente = Cliente.objects.get(email="cliente@test.com")
        medio = MedioAcreditacion.objects.get(cliente=cliente)
        self.assertEqual(medio.numero_cuenta, "12345678")

    def test_form_invalido_no_crea_cliente(self):
        response = self.client.post(self.url, {})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "clientes/form.html")
        self.assertEqual(Cliente.objects.count(), 0)
        self.assertEqual(MedioAcreditacion.objects.count(), 0)
