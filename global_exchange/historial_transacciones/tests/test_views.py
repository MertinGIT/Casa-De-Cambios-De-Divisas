from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model
from unittest import skipIf

from monedas.models import Moneda
from cotizaciones.models import TasaDeCambio
from operaciones.models import Transaccion

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
        cls.user = User.objects.create_user(
            username="tester",
            email="tester@example.com",
            password="pass12345"
        )
        cls.pyg = Moneda.objects.create(abreviacion="PYG", nombre="Guaraní", estado=True)
        cls.usd = Moneda.objects.create(abreviacion="USD", nombre="Dólar", estado=True)

        now = timezone.now()
        cls.tasa = TasaDeCambio.objects.create(
            moneda_origen=cls.pyg,
            moneda_destino=cls.usd,
            monto_compra=Decimal("7100"),
            monto_venta=Decimal("7300"),
            vigencia=now,
            estado=True,
            fecha_actualizacion=now
        )

        cls.tx = Transaccion.objects.create(
            usuario=cls.user,
            monto=Decimal("100000"),
            tipo="venta",
            estado="confirmada",
            moneda_origen=cls.pyg,
            moneda_destino=cls.usd,
            tasa_usada=Decimal("7250"),
            tasa_ref=cls.tasa
        )

    def setUp(self):
        self.client = Client()
        self.client.login(username="tester", password="pass12345")

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