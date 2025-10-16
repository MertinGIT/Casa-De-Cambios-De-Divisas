from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import Group
from cliente_usuario.models import Usuario_Cliente
from usuarios.models import CustomUser
from cliente_segmentacion.models import Segmentacion
from clientes.models import Cliente
from cliente_usuario.models import Usuario_Cliente  # ← Importar este modelo
from monedas.models import Moneda
from cotizaciones.models import TasaDeCambio
from operaciones.models import Transaccion
from metodos_pagos.models import MetodoPago  # ← AGREGAR IMPORT
from decimal import Decimal
from django.utils import timezone
from django.core import mail
from unittest.mock import patch
from django.urls import reverse

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

        # ← AGREGAR ESTA RELACIÓN Usuario_Cliente
        Usuario_Cliente.objects.create(
            id_usuario=self.user,
            id_cliente=self.cliente
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
            precio_base=Decimal("7400.00"),
            comision_compra=Decimal("0.00"),
            comision_venta=Decimal("0.00"),
        )

        # ← CREAR MÉTODO DE PAGO
        self.metodo_pago = MetodoPago.objects.create(
            nombre="Efectivo Test",
            descripcion="Pago en efectivo para tests",
            activo=True
        )

    def test_simulador_operaciones_get(self):
        url = reverse("operaciones")
        response = self.client.get(url)
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
        url = reverse("guardar_transaccion")
        payload = {
            "monto": "100",
            "tipo": "compra",
            "estado": "pendiente",
            "moneda_origen_id": self.moneda_pyg.id,
            "moneda_destino_id": self.moneda_usd.id,
            "tasa_usada": "7300",
            "tasa_ref_id": self.tasa.id,
            "cliente_id": self.cliente.id,
            "metodo_pago_id": self.metodo_pago.id  # ← AGREGAR ESTE CAMPO
        }
        response = self.client.post(url, data=payload, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(Transaccion.objects.count(), 1)
        
    @patch("operaciones.views.send_mail")  # 👈 parcheamos send_mail en la vista
    def test_enviar_pin_envia_email_y_guarda_en_sesion(self, mock_send_mail):
        url = reverse("enviar_pin")
        response = self.client.get(url, HTTP_X_REQUESTED_WITH="XMLHttpRequest")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])

        # ✅ Verificar que send_mail fue llamado
        mock_send_mail.assert_called_once()
        args, kwargs = mock_send_mail.call_args
        self.assertIn("Tu código de verificación es", args[1])  # cuerpo del mail contiene el PIN

        # ✅ Verificar que el pin se guardó en sesión
        session = self.client.session
        self.assertIn("pin_seguridad", session)
    def test_validar_pin_correcto(self):
        # Simulamos que ya hay un PIN en la sesión
        session = self.client.session
        session["pin_seguridad"] = "1234"
        session.save()

        url = reverse("validar_pin")
        response = self.client.post(url, {"pin": "1234"})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])

        # Verificar que el PIN fue eliminado de la sesión
        session = self.client.session
        self.assertNotIn("pin_seguridad", session)

    def test_validar_pin_incorrecto(self):
        # Guardamos un PIN en la sesión
        session = self.client.session
        session["pin_seguridad"] = "1234"
        session.save()

        url = reverse("validar_pin")
        response = self.client.post(url, {"pin": "0000"})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data["success"])
        self.assertIn("PIN incorrecto", data["message"])
