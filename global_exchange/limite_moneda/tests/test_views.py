# limite_moneda/tests/test_views.py
from django.test import TestCase, Client
from django.urls import reverse
from decimal import Decimal
from clientes.models import Cliente
from monedas.models import Moneda
from limite_moneda.models import LimiteTransaccion
from cliente_segmentacion.models import Segmentacion
from usuarios.models import CustomUser
import json

class LimiteTransaccionViewsTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        # Crear superadmin y login
        cls.user = CustomUser.objects.get(username="superadmin")

        # Crear segmentación
        cls.segmentacion = Segmentacion.objects.create(nombre="Segmento Test")

        # Crear cliente
        cls.cliente = Cliente.objects.create(
            nombre="Cliente Test",
            estado="activo",
            segmentacion=cls.segmentacion,
            email="cliente1@test.com"
        )

        # Crear moneda
        cls.moneda = Moneda.objects.create(nombre="Guaraní", abreviacion="PYG", estado=True)

        # Crear límite existente
        cls.limite = LimiteTransaccion.objects.create(
            cliente=cls.cliente,
            moneda=cls.moneda,
            limite_diario=Decimal("100.50"),
            limite_mensual=Decimal("1000.75"),
            estado="activo"
        )

    def setUp(self):
        self.client = Client()
        self.client.force_login(self.user)

    def test_lista_limites(self):
        url = reverse("lista-limites")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.cliente.nombre)

    def test_limite_detalle(self):
        url = reverse("limite-detalle", args=[self.limite.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["id"], self.limite.id)
        self.assertEqual(data["cliente"], self.cliente.id)

    def test_check_nombre_cliente_valido(self):
        url = reverse("check-nombre-cliente")
        response = self.client.post(url, {
            "cliente": self.cliente.id,
            "moneda": self.moneda.id,
            "obj_id": self.limite.id
        })
        data = json.loads(response.content)
        # El mismo límite editándose es válido
        self.assertTrue(data)

    def test_check_nombre_cliente_nuevo(self):
        url = reverse("check-nombre-cliente")

        # Crear un nuevo cliente con email único
        cliente2 = Cliente.objects.create(
            nombre="Cliente Test 2",
            estado="activo",
            segmentacion=self.segmentacion,
            email="cliente2@test.com"
        )

        response = self.client.post(url, {
            "cliente": cliente2.id,
            "moneda": self.moneda.id,
            "obj_id": ""
        })
        data = json.loads(response.content)
        self.assertTrue(data)  # Puede asignarse porque no hay límite activo

    def test_crear_limite_valido(self):
        url = reverse("limite-crear")
        cliente3 = Cliente.objects.create(
            nombre="Cliente Test 3",
            estado="activo",
            segmentacion=self.segmentacion,
            email="cliente3@test.com"
        )
        data = {
            "cliente": cliente3.id,
            "moneda": self.moneda.id,
            "limite_diario": "200",
            "limite_mensual": "2000"
        }
        response = self.client.post(url, data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        res_json = response.json()
        self.assertTrue(res_json["success"])
        self.assertEqual(res_json["limite"]["cliente_id"], cliente3.id)

    def test_editar_limite(self):
        url = reverse("limite-editar", args=[self.limite.id])
        data = {
            "cliente": self.cliente.id,
            "moneda": self.moneda.id,
            "limite_diario": "150",
            "limite_mensual": "1500"
        }
        response = self.client.post(url, data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        res_json = response.json()
        self.assertTrue(res_json["success"])
        self.limite.refresh_from_db()
        self.assertEqual(self.limite.limite_diario, Decimal("150"))

    def test_cambiar_estado_limite(self):
        url = reverse("limite-cambiar-estado", args=[self.limite.id])
        response = self.client.post(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        res_json = response.json()
        self.assertTrue(res_json["success"])
        self.limite.refresh_from_db()
        self.assertEqual(self.limite.estado, "inactivo")

    def test_get_clientes(self):
        url = reverse("get_clientes")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertGreaterEqual(len(data), 1)
        self.assertIn("nombre", data[0])

    def test_get_monedas(self):
        url = reverse("get_monedas")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertGreaterEqual(len(data), 1)
        self.assertIn("nombre", data[0])
