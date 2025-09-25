# operaciones/tests/test_views.py
from django.test import TestCase, Client
from django.urls import reverse
from decimal import Decimal
from usuarios.models import CustomUser
from monedas.models import Moneda
from cotizaciones.models import TasaDeCambio
from operaciones.models import Transaccion
from datetime import datetime, timedelta
from django.utils import timezone

class OperacionesViewsTest(TestCase):

    def setUp(self):
       # Cliente de pruebas
        self.client = Client()

        # Crear usuario y loguearse
        self.user = CustomUser.objects.create_user(
            username="testuser",
            password="testpass123",
            cedula="12345678"
        )
        self.client.login(username="testuser", password="testpass123")

        # Crear monedas
        self.moneda_origen = Moneda.objects.create(nombre="Dólar", abreviacion="USD", estado=True)
        self.moneda_destino = Moneda.objects.create(nombre="Guaraní", abreviacion="PYG", estado=True)

        # Crear tasa de cambio **para que PYG -> USD funcione en el test**
        self.tasa = TasaDeCambio.objects.create(
            moneda_origen=self.moneda_destino,   # PYG
            moneda_destino=self.moneda_origen,   # USD
            monto_compra=Decimal("0.00014"),     # ejemplo
            monto_venta=Decimal("0.00015"),     # ejemplo
            estado=True,
            vigencia=timezone.now()
        )

    def test_simulador_operaciones_get(self):
        """GET del simulador debe devolver 200 y contexto esperado"""
        url = reverse("operaciones")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("monedas", response.context)
        self.assertIn("transacciones", response.context)
        self.assertIn("PB_MONEDA", response.context)

    def test_simulador_operaciones_post_venta(self):
        """POST al simulador con operación 'venta' calcula resultado correctamente"""
        url = reverse("operaciones")
        data = {
            "valor": "10000",
            "operacion": "venta",
            "origen": "PYG",   # orígen puede ser PYG
            "destino": "USD"   # destino NO puede ser PYG
        }
        response = self.client.post(url, data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertIn("resultado", json_data)
        self.assertIn("ganancia_total", json_data)
        self.assertIn("tasa", json_data)

    def test_guardar_transaccion(self):
        """Guardar una transacción mediante POST"""
        url = reverse("guardar_transaccion")
        payload = {
            "monto": "5000",
            "tipo": "compra",
            "estado": "pendiente",
            "moneda_origen_id": self.moneda_origen.id,
            "moneda_destino_id": self.moneda_destino.id,
            "tasa_usada": "7100.0",
            "tasa_ref_id": self.tasa.id
        }
        response = self.client.post(url, payload, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertTrue(json_data["success"])
        self.assertTrue(Transaccion.objects.filter(id=json_data["id"]).exists())

    