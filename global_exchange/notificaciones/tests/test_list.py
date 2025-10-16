from django.test import TestCase
from django.contrib.auth import get_user_model
from decimal import Decimal
from datetime import date
from monedas.models import Moneda
from cotizaciones.models import TasaDeCambio
from notificaciones.models import NotificacionMoneda, AuditoriaTasaCambio
from clientes.models import Cliente
from cliente_segmentacion.models import Segmentacion
from cliente_usuario.models import Usuario_Cliente

User = get_user_model()


class NotificacionesIntegrationTest(TestCase):
    """Tests de integración para el flujo completo de notificaciones"""
    
    def setUp(self):
        """Configuración inicial completa"""
        # Crear usuarios
        self.user1 = User.objects.create_user(
            username="user1",
            email="user1@example.com",
            cedula="11111111",
            password="pass123"
        )
        self.user2 = User.objects.create_user(
            username="user2",
            email="user2@example.com",
            cedula="22222222",
            password="pass123"
        )
        
        # Crear monedas
        self.usd = Moneda.objects.create(nombre="Dólar", abreviacion="USD", estado=True)
        self.pyg = Moneda.objects.create(nombre="Guaraní", abreviacion="PYG", estado=True)
        self.eur = Moneda.objects.create(nombre="Euro", abreviacion="EUR", estado=True)
        
        # Crear tasa de cambio
        self.tasa = TasaDeCambio.objects.create(
            moneda_origen=self.usd,
            moneda_destino=self.pyg,
            precio_base=Decimal("7400.00"),
            comision_compra=Decimal("0.00"),
            comision_venta=Decimal("0.00"),
            vigencia=date.today(),
            estado=True
        )
        
        # Crear segmentación y clientes
        self.segmentacion_vip = Segmentacion.objects.create(
            nombre="VIP",
            estado="activo",
            descuento=20
        )
        self.segmentacion_regular = Segmentacion.objects.create(
            nombre="Regular",
            estado="activo",
            descuento=5
        )
        
        self.cliente1 = Cliente.objects.create(
            nombre="Cliente VIP",
            segmentacion=self.segmentacion_vip,
            email="vip@test.com",
            estado="activo"
        )
        self.cliente2 = Cliente.objects.create(
            nombre="Cliente Regular",
            segmentacion=self.segmentacion_regular,
            email="regular@test.com",
            estado="activo"
        )

    def test_flujo_completo_notificaciones_usuario(self):
        """Test del flujo completo: crear notificaciones para un usuario"""
        # Usuario 1 activa notificaciones para USD y EUR
        notif1 = NotificacionMoneda.objects.create(
            user=self.user1,
            moneda=self.usd,
            activa=True
        )
        notif2 = NotificacionMoneda.objects.create(
            user=self.user1,
            moneda=self.eur,
            activa=True
        )
        
        # Verificar que se crearon correctamente
        notificaciones = NotificacionMoneda.objects.filter(user=self.user1, activa=True)
        self.assertEqual(notificaciones.count(), 2)
        
        monedas_activas = [n.moneda.abreviacion for n in notificaciones]
        self.assertIn("USD", monedas_activas)
        self.assertIn("EUR", monedas_activas)

    def test_multiples_usuarios_misma_moneda(self):
        """Verifica que múltiples usuarios pueden notificarse de la misma moneda"""
        NotificacionMoneda.objects.create(
            user=self.user1,
            moneda=self.usd,
            activa=True
        )
        NotificacionMoneda.objects.create(
            user=self.user2,
            moneda=self.usd,
            activa=True
        )
        
        notifs_usd = NotificacionMoneda.objects.filter(moneda=self.usd, activa=True)
        self.assertEqual(notifs_usd.count(), 2)

    def test_relacion_usuario_cliente_notificaciones(self):
        """Test de la relación entre usuarios, clientes y notificaciones"""
        # Asociar usuarios con clientes
        Usuario_Cliente.objects.create(
            id_usuario=self.user1,
            id_cliente=self.cliente1
        )
        Usuario_Cliente.objects.create(
            id_usuario=self.user2,
            id_cliente=self.cliente2
        )
        
        # Activar notificaciones
        NotificacionMoneda.objects.create(
            user=self.user1,
            moneda=self.usd,
            activa=True
        )
        NotificacionMoneda.objects.create(
            user=self.user2,
            moneda=self.eur,
            activa=True
        )
        
        # Verificar que cada usuario tiene su cliente y notificaciones
        cliente_user1 = Usuario_Cliente.objects.get(id_usuario=self.user1).id_cliente
        self.assertEqual(cliente_user1.nombre, "Cliente VIP")
        
        notif_user1 = NotificacionMoneda.objects.get(user=self.user1)
        self.assertEqual(notif_user1.moneda.abreviacion, "USD")

    def test_desactivar_y_reactivar_notificacion(self):
        """Test del ciclo de vida de una notificación"""
        # Crear notificación activa
        notif = NotificacionMoneda.objects.create(
            user=self.user1,
            moneda=self.usd,
            activa=True
        )
        
        self.assertTrue(notif.activa)
        
        # Desactivar
        notif.activa = False
        notif.save()
        
        notif.refresh_from_db()
        self.assertFalse(notif.activa)
        
        # Reactivar
        notif.activa = True
        notif.save()
        
        notif.refresh_from_db()
        self.assertTrue(notif.activa)

    def test_listado_notificaciones_por_usuario(self):
        """Verifica que se pueden listar todas las notificaciones de un usuario"""
        # Crear varias notificaciones
        NotificacionMoneda.objects.create(user=self.user1, moneda=self.usd, activa=True)
        NotificacionMoneda.objects.create(user=self.user1, moneda=self.eur, activa=False)
        NotificacionMoneda.objects.create(user=self.user1, moneda=self.pyg, activa=True)
        
        # Listar todas
        todas = NotificacionMoneda.objects.filter(user=self.user1)
        self.assertEqual(todas.count(), 3)
        
        # Listar solo activas
        activas = NotificacionMoneda.objects.filter(user=self.user1, activa=True)
        self.assertEqual(activas.count(), 2)

    def test_auditoria_calculo_porcentaje_variacion(self):
        """Verifica el cálculo de porcentajes en diferentes escenarios"""
        # Aumento del 10%
        auditoria1 = AuditoriaTasaCambio.objects.create(
            tasa=self.tasa,
            tipo_cambio='EDICION',
            precio_anterior=Decimal("7000.00"),
            precio_nuevo=Decimal("7700.00"),
            vigencia_nueva=date.today(),
            estado_nuevo=True
        )
        self.assertEqual(auditoria1.porcentaje_cambio(), 10)
        
        # Disminución del 5%
        auditoria2 = AuditoriaTasaCambio.objects.create(
            tasa=self.tasa,
            tipo_cambio='EDICION',
            precio_anterior=Decimal("8000.00"),
            precio_nuevo=Decimal("7600.00"),
            vigencia_nueva=date.today(),
            estado_nuevo=True
        )
        self.assertEqual(auditoria2.porcentaje_cambio(), 5)

    def test_monedas_estado_inactivo_no_aparecen(self):
        """Verifica que las monedas inactivas no se muestran"""
        moneda_inactiva = Moneda.objects.create(
            nombre="Libra",
            abreviacion="GBP",
            estado=False
        )
        
        monedas_activas = Moneda.objects.filter(estado=True)
        self.assertNotIn(moneda_inactiva, monedas_activas)
        
        # Las 3 monedas activas creadas en setUp
        self.assertEqual(monedas_activas.count(), 3)