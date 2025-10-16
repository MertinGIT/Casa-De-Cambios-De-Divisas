from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from cotizaciones.models import TasaDeCambio, Moneda
from usuarios.models import CustomUser
from decimal import Decimal

class CotizacionViewsTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        """Configuración inicial de datos de prueba"""
        # Obtener superusuario existente
        cls.superadmin = CustomUser.objects.get(username='superadmin')
        
        # Crear monedas
        cls.guarani = Moneda.objects.create(
            nombre="Guaraní",
            abreviacion="PYG",
            estado=True
        )
        cls.dolar = Moneda.objects.create(
            nombre="Dólar",
            abreviacion="USD",
            estado=True
        )
        cls.euro = Moneda.objects.create(
            nombre="Euro",
            abreviacion="EUR",
            estado=True
        )
        
        # Crear tasa de prueba
        cls.tasa = TasaDeCambio.objects.create(
            moneda_origen=cls.guarani,
            moneda_destino=cls.dolar,
            precio_base=Decimal("7400.00"),
            comision_compra=Decimal("10.00"),
            comision_venta=Decimal("15.00"),
            vigencia=timezone.now(),
            estado=True
        )

    def setUp(self):
        self.client = Client()
        self.client.login(username='superadmin', password='ContraseñaSegura123')

    def test_cotizacion_lista_view(self):
        url = reverse("cotizacion")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("tasas", response.context)

    def test_cotizacion_lista_busqueda(self):
        url = reverse("cotizacion") + "?q=Dólar&campo=moneda_destino"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_cotizacion_nuevo_post_invalido_ajax(self):
        url = reverse("cotizacion_nuevo")
        response = self.client.post(url, {}, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertFalse(json_data["success"])
        self.assertIn("errors", json_data)

    def test_cotizacion_editar_post_invalido_ajax(self):
        url = reverse("cotizacion_editar", args=[self.tasa.id])
        response = self.client.post(url, {}, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertFalse(json_data["success"])

    def test_cotizacion_desactivar(self):
        url = reverse("cotizacion_desactivar", args=[self.tasa.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.tasa.refresh_from_db()
        self.assertFalse(self.tasa.estado)

    def test_cotizacion_detalle(self):
        url = reverse("cotizacion_detalle", args=[self.tasa.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertEqual(json_data["id"], self.tasa.id)
        self.assertEqual(json_data["moneda_origen"], self.guarani.id)
        self.assertEqual(json_data["moneda_destino"], self.dolar.id)
        self.assertEqual(Decimal(str(json_data["precio_base"])), self.tasa.precio_base)
        self.assertIn("monto_compra", json_data)
        self.assertIn("monto_venta", json_data)
        self.assertIn("vigencia", json_data)