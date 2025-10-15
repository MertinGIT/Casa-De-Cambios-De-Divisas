from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model
from unittest import skipIf

from monedas.models import Moneda
from cotizaciones.models import TasaDeCambio
from operaciones.models import Transaccion
from clientes.models import Cliente
from cliente_segmentacion.models import Segmentacion

User = get_user_model()

# Dependencias opcionales (no deben hacer fallar los tests)
try:
    import openpyxl  # noqa
    HAS_OPENPYXL = True
except ImportError:
    HAS_OPENPYXL = False

try:
    import reportlab  # noqa
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False


class HistorialTransaccionesViewsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.get(username="superadmin")

        cls.pyg = Moneda.objects.create(abreviacion="PYG", nombre="Guaraní", estado=True)
        cls.usd = Moneda.objects.create(abreviacion="USD", nombre="Dólar", estado=True)

        now = timezone.now()
        # Usar precio_base y comisiones en lugar de monto_compra/monto_venta
        cls.tasa = TasaDeCambio.objects.create(
            moneda_origen=cls.pyg,
            moneda_destino=cls.usd,
            precio_base=Decimal("7200.00"),
            comision_compra=Decimal("100.00"),
            comision_venta=Decimal("100.00"),
            vigencia=now,
            estado=True
        )

        # Crear segmentación requerida para Cliente
        cls.segmentacion = Segmentacion.objects.create(
            nombre="Estándar",
            descripcion="Segmentación por defecto",
            descuento=0.0,
            estado="activo"
        )

        # Crear cliente para la transacción (según modelo real)
        cls.cliente = Cliente.objects.create(
            nombre="Cliente Test",
            cedula="1234567",
            email="cliente@test.com",
            telefono="0981234567",
            segmentacion=cls.segmentacion,
            estado="activo"
        )

        # Crear transacción con los campos CORRECTOS según operaciones/models.py
        cls.tx = Transaccion.objects.create(
            usuario=cls.user,
            cliente=cls.cliente,
            monto=Decimal("100000"),           # ✅ campo correcto
            tipo="venta",                       # ✅ campo correcto (no tipo_operacion)
            estado="confirmada",
            moneda_origen=cls.pyg,
            moneda_destino=cls.usd,
            tasa_usada=Decimal("7250"),        # ✅ campo correcto (no tasa_aplicada)
            tasa_ref=cls.tasa,                 # ✅ campo correcto (no tasa)
            fecha=now
        )

    def setUp(self):
        self.client = Client()
        self.client.login(username="superadmin", password="ContraseñaSegura123")

    def test_historial_usuario_ok(self):
        url = reverse("historial_transacciones:historial_usuario")
        r = self.client.get(url)
        self.assertEqual(r.status_code, 200)
        self.assertIn(str(self.tx.id), r.content.decode())

    def test_historial_filtro_moneda(self):
        url = reverse("historial_transacciones:historial_usuario")
        r = self.client.get(url, {"moneda": "USD"})
        self.assertEqual(r.status_code, 200)
        self.assertIn("USD", r.content.decode())

    def test_historial_buscar_id(self):
        url = reverse("historial_transacciones:historial_usuario")
        r = self.client.get(url, {"q": str(self.tx.id), "campo": "id"})
        self.assertEqual(r.status_code, 200)
        self.assertIn(str(self.tx.id), r.content.decode())

    @skipIf(not HAS_OPENPYXL, "openpyxl no instalado (se omite, no falla)")
    def test_exportar_excel(self):
        url = reverse("historial_transacciones:exportar_historial_excel")
        r = self.client.get(url)
        self.assertEqual(r.status_code, 200)
        self.assertIn(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            r.headers.get("Content-Type", "")
        )

    @skipIf(not HAS_REPORTLAB, "reportlab no instalado (se omite, no falla)")
    def test_exportar_pdf(self):
        url = reverse("historial_transacciones:exportar_historial_pdf")
        r = self.client.get(url)
        self.assertEqual(r.status_code, 200)
        self.assertIn("application/pdf", r.headers.get("Content-Type", ""))