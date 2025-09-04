from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from monedas.models import Moneda
from .models import TasaDeCambio

User = get_user_model()


class TasaDeCambioModelTest(TestCase):
    def setUp(self):
        self.moneda1 = Moneda.objects.create(nombre="Dólar", abreviacion="USD")
        self.moneda2 = Moneda.objects.create(nombre="Euro", abreviacion="EUR")
        self.tasa = TasaDeCambio.objects.create(
            moneda_origen=self.moneda1,
            moneda_destino=self.moneda2,
            monto_compra=7000.50,
            monto_venta=7100.75,
            vigencia=timezone.now()
        )

    def test_str_representation(self):
        expected = f"{self.moneda1}/{self.moneda2} - Compra: {self.tasa.monto_compra} Venta: {self.tasa.monto_venta}"
        self.assertEqual(str(self.tasa), expected)


class TasaDeCambioViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="admin", password="12345", is_superuser=True)
        self.client.login(username="admin", password="12345")
        self.moneda1 = Moneda.objects.create(nombre="Dólar", abreviacion="USD")
        self.moneda2 = Moneda.objects.create(nombre="Euro", abreviacion="EUR")
        self.tasa = TasaDeCambio.objects.create(
            moneda_origen=self.moneda1,
            moneda_destino=self.moneda2,
            monto_compra=7000.50,
            monto_venta=7100.75,
            vigencia=timezone.now()
        )

    def test_cotizacion_lista_view(self):
        response = self.client.get(reverse("cotizacion"))
        self.assertEqual(response.status_code, 200)

    def test_cotizacion_nuevo_view(self):
        response = self.client.post(reverse("cotizacion_nuevo"), {
            "moneda_origen": self.moneda1.id,
            "moneda_destino": self.moneda2.id,
            "monto_compra": 7200.0,
            "monto_venta": 7300.0,
            "vigencia": timezone.now()
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(TasaDeCambio.objects.count(), 2)

    def test_cotizacion_editar_view(self):
        new_compra = 7500.0
        response = self.client.post(reverse("cotizacion_editar", args=[self.tasa.id]), {
            "moneda_origen": self.moneda1.id,
            "moneda_destino": self.moneda2.id,
            "monto_compra": new_compra,
            "monto_venta": self.tasa.monto_venta,
            "vigencia": self.tasa.vigencia
        })
        self.assertEqual(response.status_code, 302)
        self.tasa.refresh_from_db()
        self.assertEqual(float(self.tasa.monto_compra), new_compra)

    def test_cotizacion_eliminar_view(self):
        response = self.client.post(reverse("cotizacion_eliminar", args=[self.tasa.id]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(TasaDeCambio.objects.filter(id=self.tasa.id).exists())

    def test_cotizacion_detalle_view(self):
        response = self.client.get(reverse("cotizacion_detalle", args=[self.tasa.id]))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["id"], self.tasa.id)
        self.assertEqual(data["moneda_origen"], self.moneda1.id)
        self.assertEqual(data["moneda_destino"], self.moneda2.id)
