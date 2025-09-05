from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from cotizaciones.models import TasaDeCambio, Moneda


class CotizacionViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        # Creamos monedas de prueba
        self.origen = Moneda.objects.create(nombre="Guaraní", abreviacion="PYG", estado=True)
        self.destino = Moneda.objects.create(nombre="Dólar", abreviacion="USD", estado=True)

        # Creamos una tasa de cambio inicial
        self.tasa = TasaDeCambio.objects.create(
            moneda_origen=self.origen,
            moneda_destino=self.destino,
            monto_compra=7000,
            monto_venta=7200,
            vigencia=timezone.now(),
            estado=True,
        )

    # ------------------------
    # cotizacion_lista
    # ------------------------
    def test_cotizacion_lista_view(self):
        url = reverse("cotizacion")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("tasas", response.context)
        self.assertIn(self.tasa, response.context["tasas"])

    def test_cotizacion_lista_busqueda(self):
        url = reverse("cotizacion") + "?q=Dólar&campo=moneda_destino"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.tasa, response.context["tasas"])

    # ------------------------
    # cotizacion_nuevo
    # ------------------------
    def test_cotizacion_nuevo_post_valido_ajax(self):
        url = reverse("cotizacion_nuevo")
        data = {
            "moneda_origen": self.origen.id,
            "moneda_destino": self.destino.id,
            "monto_compra": "7100.00",
            "monto_venta": "7300.00",
            "vigencia": timezone.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        response = self.client.post(url, data, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(response.status_code, 200)
        json = response.json()
        self.assertTrue(json["success"])
        self.assertEqual(json["tasa"]["origen"], "PYG")

    def test_cotizacion_nuevo_post_invalido_ajax(self):
        url = reverse("cotizacion_nuevo")
        response = self.client.post(url, {}, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(response.status_code, 200)
        json = response.json()
        self.assertFalse(json["success"])
        self.assertIn("errors", json)

    # ------------------------
    # cotizacion_editar
    # ------------------------
    def test_cotizacion_editar_post_valido_ajax(self):
        url = reverse("cotizacion_editar", args=[self.tasa.id])
        data = {
            "moneda_origen": self.origen.id,
            "moneda_destino": self.destino.id,
            "monto_compra": "7050.00",
            "monto_venta": "7250.00",
            "vigencia": timezone.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        response = self.client.post(url, data, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(response.status_code, 200)
        json = response.json()
        self.assertTrue(json["success"])
        self.assertEqual(json["tasa"]["compra"], "7050.00")

    def test_cotizacion_editar_post_invalido_ajax(self):
        url = reverse("cotizacion_editar", args=[self.tasa.id])
        response = self.client.post(url, {}, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(response.status_code, 200)
        json = response.json()
        self.assertFalse(json["success"])

    # ------------------------
    # cotizacion_desactivar
    # ------------------------
    def test_cotizacion_desactivar(self):
        url = reverse("cotizacion_desactivar", args=[self.tasa.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)  # redirección
        self.tasa.refresh_from_db()
        self.assertFalse(self.tasa.estado)

    # ------------------------
    # cotizacion_detalle
    # ------------------------
    def test_cotizacion_detalle(self):
        url = reverse("cotizacion_detalle", args=[self.tasa.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        json = response.json()
        self.assertEqual(json["id"], self.tasa.id)
        self.assertEqual(json["moneda_origen"], self.origen.id)
        self.assertEqual(json["moneda_destino"], self.destino.id)
