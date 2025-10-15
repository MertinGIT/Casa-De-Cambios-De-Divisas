from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import Group
from usuarios.models import CustomUser
from cliente_segmentacion.models import Segmentacion
from clientes.models import Cliente
from monedas.models import Moneda
from cotizaciones.models import TasaDeCambio
from operaciones.models import Transaccion
from decimal import Decimal
from django.utils import timezone


class OperacionesViewsTest(TestCase):

    def setUp(self):
        self.group_admin, _ = Group.objects.get_or_create(name="ADMIN")
        self.group_usuario_asociado, _ = Group.objects.get_or_create(name="Usuario Asociado")

        self.user = CustomUser.objects.create_user(username="testuser", password="12345")
        self.user.groups.add(self.group_usuario_asociado)
        self.user.save()

        self.segmentacion = Segmentacion.objects.create(nombre="Segmento Test", estado="activo", descuento=10)
        self.cliente = Cliente.objects.create(
            nombre="Cliente Test",
            segmentacion=self.segmentacion,
            email="cliente@test.com",
            estado="activo"
        )

        self.client = Client()
        self.client.login(username="testuser", password="12345")
        session = self.client.session
        session['cliente_operativo_id'] = self.cliente.id
        session.save()

        self.moneda_usd = Moneda.objects.create(nombre="Dólar", abreviacion="USD", estado=True)
        self.moneda_pyg = Moneda.objects.create(nombre="Guaraní", abreviacion="PYG", estado=True)

        self.tasa = TasaDeCambio.objects.create(
            moneda_origen=self.moneda_usd,
            moneda_destino=self.moneda_pyg,
            # monto_compra=Decimal("7300.00"),
            # monto_venta=Decimal("7500.00"),
            precio_base=Decimal("7400.00"),
            comision_compra=Decimal("0.00"),
            comision_venta=Decimal("0.00"),
        )

    def test_simulador_operaciones_get(self):
        url = reverse("operaciones")  # sin namespace
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.status_code, 200)


    def test_simulador_operaciones_post_venta(self):
        url = reverse("operaciones")
        response = self.client.post(
            url,
            {"operacion": "venta", "valor": "1000", "origen": "PYG", "destino": "USD"},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("resultado", data)
        self.assertIn("ganancia_total", data)

    def test_guardar_transaccion(self):
        url = reverse("guardar_transaccion")  # sin namespace
        payload = {
            "monto": "1000",
            "tipo": "venta",
            "estado": "pendiente",
            "moneda_origen_id": self.moneda_pyg.id,
            "moneda_destino_id": self.moneda_usd.id,
            "tasa_usada": "7300",
            "tasa_ref_id": self.tasa.id
        }
        response = self.client.post(url, data=payload, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(Transaccion.objects.count(), 1)
