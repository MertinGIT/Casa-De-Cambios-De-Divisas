from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
import json
from decimal import Decimal
from monedas.models import Moneda
from notificaciones.models import NotificacionMoneda
from clientes.models import Cliente
from cliente_segmentacion.models import Segmentacion
from cliente_usuario.models import Usuario_Cliente

User = get_user_model()


class NotificacionesViewsTest(TestCase):
    
    def setUp(self):
        """Configuración inicial para los tests de vistas"""
        self.client = Client()
        
        # Crear grupo de usuarios
        self.grupo_usuario, _ = Group.objects.get_or_create(name="Usuario")
        
        # Crear usuario
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            cedula="12345678",
            password="testpass123"
        )
        self.user.groups.add(self.grupo_usuario)
        
        # Crear monedas
        self.moneda_usd = Moneda.objects.create(
            nombre="Dólar",
            abreviacion="USD",
            estado=True
        )
        self.moneda_pyg = Moneda.objects.create(
            nombre="Guaraní",
            abreviacion="PYG",
            estado=True
        )
        self.moneda_eur = Moneda.objects.create(
            nombre="Euro",
            abreviacion="EUR",
            estado=True
        )
        
        # Crear segmentación y cliente
        self.segmentacion = Segmentacion.objects.create(
            nombre="VIP",
            estado="activo",
            descuento=15
        )
        self.cliente = Cliente.objects.create(
            nombre="Cliente Test",
            segmentacion=self.segmentacion,
            email="cliente@test.com",
            estado="activo"
        )
        
        # Asociar cliente con usuario
        Usuario_Cliente.objects.create(
            id_usuario=self.user,
            id_cliente=self.cliente
        )
        
        # Login
        self.client.login(username="testuser", password="testpass123")

    def test_panel_alertas_get(self):
        """Verifica que el panel de alertas carga correctamente"""
        url = reverse("notificaciones")
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "notificaciones/configuracionAlertas.html")
        self.assertIn("monedas", response.context)
        self.assertIn("monedas_activas", response.context)
        self.assertIn("segmento", response.context)

    def test_panel_alertas_muestra_monedas_activas(self):
        """Verifica que el panel muestra las monedas con notificaciones activas"""
        # Crear notificación activa
        NotificacionMoneda.objects.create(
            user=self.user,
            moneda=self.moneda_usd,
            activa=True
        )
        
        url = reverse("notificaciones")
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn("USD", response.context["monedas_activas"])

    def test_panel_alertas_con_segmentacion(self):
        """Verifica que el panel muestra la segmentación del cliente"""
        # Establecer cliente operativo en sesión
        session = self.client.session
        session['cliente_operativo_id'] = self.cliente.id
        session.save()
        
        url = reverse("notificaciones")
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["segmento"], "VIP")
        self.assertEqual(response.context["descuento"], 15.0)

    def test_guardar_configuracion_post_valido(self):
        """Verifica que se puede guardar la configuración de notificaciones"""
        url = reverse("guardar_configuracion")
        data = {
            "monedas": [
                {"moneda": "USD", "activa": True},
                {"moneda": "EUR", "activa": False}
            ],
            "notificaciones": True
        }
        
        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type="application/json"
        )
        
        self.assertEqual(response.status_code, 200)
        json_response = response.json()
        self.assertEqual(json_response["status"], "ok")
        
        # Verificar que se crearon las notificaciones
        notif_usd = NotificacionMoneda.objects.get(user=self.user, moneda=self.moneda_usd)
        self.assertTrue(notif_usd.activa)
        
        notif_eur = NotificacionMoneda.objects.get(user=self.user, moneda=self.moneda_eur)
        self.assertFalse(notif_eur.activa)

    def test_guardar_configuracion_asegura_pyg_activa(self):
        """Verifica que PYG siempre queda activa"""
        url = reverse("guardar_configuracion")
        data = {
            "monedas": [
                {"moneda": "PYG", "activa": False}
            ],
            "notificaciones": True
        }
        
        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type="application/json"
        )
        
        self.assertEqual(response.status_code, 200)
        
        # PYG debe estar activa siempre
        notif_pyg = NotificacionMoneda.objects.get(user=self.user, moneda=self.moneda_pyg)
        self.assertTrue(notif_pyg.activa)

    def test_guardar_configuracion_update_or_create(self):
        """Verifica que actualiza notificaciones existentes"""
        # Crear notificación previa
        NotificacionMoneda.objects.create(
            user=self.user,
            moneda=self.moneda_usd,
            activa=True
        )
        
        url = reverse("guardar_configuracion")
        data = {
            "monedas": [
                {"moneda": "USD", "activa": False}
            ],
            "notificaciones": True
        }
        
        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type="application/json"
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Verificar que se actualizó
        notif_usd = NotificacionMoneda.objects.get(user=self.user, moneda=self.moneda_usd)
        self.assertFalse(notif_usd.activa)
        
        # Debe haber solo 2 registros (USD + PYG automático)
        self.assertEqual(NotificacionMoneda.objects.filter(user=self.user).count(), 2)

    def test_guardar_configuracion_metodo_no_permitido(self):
        """Verifica que solo acepta método POST"""
        url = reverse("guardar_configuracion")
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 405)
        json_response = response.json()
        self.assertEqual(json_response["status"], "error")

    def test_guardar_configuracion_moneda_no_existe(self):
        """Verifica que ignora monedas que no existen"""
        url = reverse("guardar_configuracion")
        data = {
            "monedas": [
                {"moneda": "XYZ", "activa": True}  # Moneda inexistente
            ],
            "notificaciones": True
        }
        
        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type="application/json"
        )
        
        self.assertEqual(response.status_code, 200)
        # No debe crear notificación para moneda inexistente
        self.assertFalse(
            NotificacionMoneda.objects.filter(user=self.user, moneda__abreviacion="XYZ").exists()
        )

    def test_set_cliente_operativo_valido(self):
        """Verifica que se puede establecer un cliente operativo"""
        url = reverse("set_cliente_operativo")
        response = self.client.post(url, {"cliente_id": self.cliente.id})
        
        self.assertEqual(response.status_code, 200)
        json_response = response.json()
        
        self.assertTrue(json_response["success"])
        self.assertEqual(json_response["segmento"], "VIP")
        self.assertEqual(json_response["descuento"], 15.0)
        self.assertEqual(json_response["cliente_nombre"], "Cliente Test")
        
        # Verificar que se guardó en sesión
        self.assertEqual(self.client.session['cliente_operativo_id'], self.cliente.id)

    def test_set_cliente_operativo_sin_cliente_id(self):
        """Verifica que devuelve error si no se envía cliente_id"""
        url = reverse("set_cliente_operativo")
        response = self.client.post(url, {})
        
        self.assertEqual(response.status_code, 400)
        json_response = response.json()
        self.assertFalse(json_response["success"])