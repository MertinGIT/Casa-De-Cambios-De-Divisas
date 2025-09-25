from django.test import TestCase
from django.urls import reverse
from clientes.models import Cliente
from medio_acreditacion.models import MedioAcreditacion, TipoEntidadFinanciera
from monedas.models import Moneda
from cliente_segmentacion.models import Segmentacion
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

class ClienteCreateViewTest(TestCase):
    def setUp(self):
        self.url_cliente = reverse("clientes-agregar")
        self.url_medio = reverse("medio_acreditacion_create")
        User = get_user_model()
        self.user = User.objects.create_superuser(
            username="testadmin",
            password="12345",
            email="admin@test.com"
        )
        # Crear grupo ADMIN y agregar el usuario
        admin_group, created = Group.objects.get_or_create(name="ADMIN")
        self.user.groups.add(admin_group)
        self.client.login(username="testadmin", password="12345")

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
            "tipo_cuenta": "CORRIENTE",
            "titular": "Cliente Test",
            "documento_titular": "1234567",
            "moneda": self.moneda.id,
        }

    def test_crear_cliente_y_medio_exitoso(self):
        # Crear cliente
        response_cliente = self.client.post(self.url_cliente, self.valid_cliente_data)
        self.assertRedirects(response_cliente, reverse("clientes"))
        self.assertTrue(Cliente.objects.filter(email="cliente@test.com").exists())
        cliente = Cliente.objects.get(email="cliente@test.com")
        # Crear medio de acreditación asociado al cliente
        medio_data = self.valid_medio_data.copy()
        medio_data["cliente"] = cliente.id
        response_medio = self.client.post(f"{self.url_medio}?cliente_id={cliente.id}", medio_data)
        self.assertRedirects(response_medio, f"{reverse('medio_acreditacion_list')}?cliente_id={cliente.id}")
        self.assertTrue(MedioAcreditacion.objects.filter(cliente=cliente).exists())
        medio = MedioAcreditacion.objects.get(cliente=cliente)
        self.assertEqual(medio.numero_cuenta, "12345678")

    def test_form_invalido_no_crea_cliente(self):
        response = self.client.post(self.url_cliente, {})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "clientes/form.html")
        self.assertEqual(Cliente.objects.count(), 0)
        self.assertEqual(MedioAcreditacion.objects.count(), 0)
