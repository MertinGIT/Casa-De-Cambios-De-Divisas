from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

from facturacion.models import Factura, RangoFacturacion
from operaciones.models import Transaccion
from clientes.models import Cliente
from cliente_segmentacion.models import Segmentacion
from cotizaciones.models import TasaDeCambio
from monedas.models import Moneda
from metodos_pagos.models import MetodoPago

from unittest.mock import patch
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta
from django.conf import settings

User = get_user_model()


class FacturacionViewsTest(TestCase):
    def setUp(self):
        self.client = Client()

        # 🔥 Inyectar API KEY válida para todas las requests
        self.api_headers = {
            "HTTP_X_API_KEY": settings.FACTURA_SEGURA.get("API_KEY", "TESTKEY"),
            "HTTP_X_CDC": "FAKECDC"
        }

        self.user = User.objects.create_user(
            username="testuser", password="pass"
        )
        self.client.force_login(self.user)

        self.cdc1 = "01025957333001003000065412025112810806207324"
        self.cdc2 = "01025957333001003000067212025112819516494120"
        self.ruc_emisor = "2595733"

        self.segmentacion = Segmentacion.objects.create(
            nombre="Segmento Test",
            estado="activo",
            descuento=0
        )

        self.cliente = Cliente.objects.create(
            nombre="Cliente Test",
            email="cliente@test.com",
            cedula="1234567",
            estado="activo",
            segmentacion=self.segmentacion
        )

        self.moneda = Moneda.objects.create(
            nombre="Guaraní", abreviacion="PYG"
        )

        self.metodo_pago, _ = MetodoPago.objects.get_or_create(nombre="Efectivo")

        self.tasa1 = TasaDeCambio.objects.create(
            moneda_origen=self.moneda,
            moneda_destino=self.moneda,
            precio_base=Decimal('1.0'),
            comision_compra=Decimal('0.00'),
            comision_venta=Decimal('0.00'),
            vigencia=timezone.now() - timedelta(days=1),
            estado=True
        )

        self.tasa2 = TasaDeCambio.objects.create(
            moneda_origen=self.moneda,
            moneda_destino=self.moneda,
            precio_base=Decimal('1.2'),
            comision_compra=Decimal('0.00'),
            comision_venta=Decimal('0.00'),
            vigencia=timezone.now(),
            estado=True
        )

        self.rango = RangoFacturacion.objects.create(
            establecimiento="001",
            punto_expedicion="003",
            numero_inicio=651,
            numero_fin=660,
            numero_actual=651,
            usuario=self.user,
            activo=True
        )

        self.transaccion = Transaccion.objects.create(
            id=50,
            cliente=self.cliente,
            monto=Decimal('10000.00'),
            moneda_origen=self.moneda,
            moneda_destino=self.moneda,
            tasa_usada=Decimal('1.0'),
            tasa_ref=self.tasa2,
            metodo_pago=self.metodo_pago,
            tipo="venta"
        )

        self.factura = Factura.objects.create(
            numero="001-003-0000001",
            cdc=self.cdc1,
            cliente=self.cliente,
            transaccion=self.transaccion,
            monto_total=Decimal('10000.00'),
            moneda="PYG",
            tipo_cambio=Decimal('1.0'),
            estado="pendiente",
            creado_por=self.user,
            rango_utilizado=self.rango,
            establecimiento="001",
            punto_expedicion="003",
            numero_documento="0000001"
        )

    # ============================================================
    # TESTS CONSULTAR ESTADO
    # ============================================================

    def test_consultar_estado_factura_success(self):
        with patch("facturacion.views.FacturaSeguraService.consultar_estado") as mock_estado:
            mock_estado.return_value = {
                'estado_sifen': 'Aprobado',
                'desc_sifen': 'Aprobada',
            }

            url = reverse("consultar_estado", args=[self.factura.id])
            resp = self.client.get(url, **self.api_headers)

            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            self.assertTrue(data["success"])
            self.assertEqual(data["estado"], "aprobado")
            self.assertEqual(data["estado_sifen"], "Aprobado")
            self.assertEqual(data["cdc"], self.cdc1)

    def test_consultar_estado_factura_not_found(self):
        url = reverse("consultar_estado", args=[9999])
        resp = self.client.get(url, **self.api_headers)

        self.assertEqual(resp.status_code, 404)

        if resp["Content-Type"].startswith("application/json"):
            data = resp.json()
            self.assertFalse(data["success"])
            self.assertIn("no encontrada", data["error"].lower())

    def test_consultar_estado_factura_transaccion_success(self):
        with patch("facturacion.views.FacturaSeguraService.consultar_estado") as mock_estado:
            mock_estado.return_value = {
                'estado_sifen': 'Aprobado',
                'desc_sifen': 'Aprobada',
            }

            url = reverse("consultar_factura_transaccion")
            resp = self.client.get(url,
                                   {"transaccion_id": self.transaccion.id},
                                   **self.api_headers)

            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            self.assertTrue(data["success"])
            self.assertEqual(data["estado"]["estado_sifen"], "Aprobado")
            self.assertEqual(data["cdc"], self.cdc1)

    def test_consultar_estado_factura_transaccion_no_factura(self):
        url = reverse("consultar_factura_transaccion")
        resp = self.client.get(url,
                               {"transaccion_id": 9999},
                               **self.api_headers)

        self.assertEqual(resp.status_code, 404)

        if resp["Content-Type"].startswith("application/json"):
            data = resp.json()
            self.assertFalse(data["success"])
            self.assertIn("no tiene factura", data["error"].lower())

    # ============================================================
    # TESTS DESCARGA FACTURA
    # ============================================================

    def test_descargar_factura_success(self):
        cdc = self.cdc1
        transaccion = self.transaccion
        pdf_path = f"/tmp/kude_{cdc}.pdf"

        with open(pdf_path, "wb") as f:
            f.write(b"PDFDATA")

        with patch("facturacion.views.FacturaSeguraService.descargar_kude") as mock_kude:
            mock_kude.return_value = True

            with patch("facturacion.views.open", create=True) as mock_open:
                mock_open.return_value = open(pdf_path, "rb")

                url = reverse("descargar_factura")
                resp = self.client.get(
                    url,
                    {"cdc": cdc, "transaccion_id": transaccion.id},
                    **self.api_headers
                )

                self.assertEqual(resp.status_code, 200)
                self.assertEqual(resp["Content-Type"], "application/pdf")
                self.assertTrue(resp["Content-Disposition"].startswith("attachment;"))

    def test_descargar_factura_not_found(self):
        url = reverse("descargar_factura")
        resp = self.client.get(
            url,
            {"cdc": self.cdc1, "transaccion_id": 9999},
            **self.api_headers
        )

        self.assertEqual(resp.status_code, 404)

        if resp["Content-Type"].startswith("application/json"):
            data = resp.json()
            self.assertFalse(data["success"])
            self.assertIn("no encontrada", data["error"].lower())

    def test_descargar_factura_missing_params(self):
        url = reverse("descargar_factura")
        resp = self.client.get(
            url,
            {"cdc": ""},
            **self.api_headers
        )

        self.assertEqual(resp.status_code, 400)

        if resp["Content-Type"].startswith("application/json"):
            data = resp.json()
            self.assertFalse(data["success"])
            self.assertIn("faltan", data["error"].lower())
