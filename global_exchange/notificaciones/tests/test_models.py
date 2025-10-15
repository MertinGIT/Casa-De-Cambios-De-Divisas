from django.test import TestCase
from django.contrib.auth import get_user_model
from decimal import Decimal
from datetime import date, timedelta
from django.utils import timezone
from monedas.models import Moneda
from cotizaciones.models import TasaDeCambio
from notificaciones.models import NotificacionMoneda, AuditoriaTasaCambio

User = get_user_model()


class NotificacionMonedaModelTest(TestCase):
    
    def setUp(self):
        """Configuración inicial para los tests"""
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            cedula="12345678",
            password="testpass123"
        )
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

    def test_crear_notificacion_moneda(self):
        """Verifica que se puede crear una notificación de moneda"""
        notif = NotificacionMoneda.objects.create(
            user=self.user,
            moneda=self.moneda_usd,
            activa=True
        )
        self.assertEqual(notif.user, self.user)
        self.assertEqual(notif.moneda, self.moneda_usd)
        self.assertTrue(notif.activa)
        self.assertIsNotNone(notif.creado)
        self.assertIsNotNone(notif.actualizado)

    def test_str_method_notificacion(self):
        """Verifica el método __str__ de NotificacionMoneda"""
        notif = NotificacionMoneda.objects.create(
            user=self.user,
            moneda=self.moneda_usd,
            activa=True
        )
        expected = f"{self.user.username} → {self.moneda_usd.abreviacion}"
        self.assertEqual(str(notif), expected)

    def test_unique_together_constraint(self):
        """Verifica que no se pueden crear notificaciones duplicadas para el mismo usuario y moneda"""
        NotificacionMoneda.objects.create(
            user=self.user,
            moneda=self.moneda_usd,
            activa=True
        )
        
        # Intentar crear duplicado debe fallar
        with self.assertRaises(Exception):
            NotificacionMoneda.objects.create(
                user=self.user,
                moneda=self.moneda_usd,
                activa=False
            )

    def test_multiples_notificaciones_diferentes_monedas(self):
        """Verifica que un usuario puede tener notificaciones para múltiples monedas"""
        NotificacionMoneda.objects.create(
            user=self.user,
            moneda=self.moneda_usd,
            activa=True
        )
        NotificacionMoneda.objects.create(
            user=self.user,
            moneda=self.moneda_pyg,
            activa=True
        )
        
        notificaciones = NotificacionMoneda.objects.filter(user=self.user)
        self.assertEqual(notificaciones.count(), 2)

    def test_notificacion_activa_default_true(self):
        """Verifica que el campo activa tiene valor por defecto True"""
        notif = NotificacionMoneda.objects.create(
            user=self.user,
            moneda=self.moneda_usd
        )
        self.assertTrue(notif.activa)


class AuditoriaTasaCambioModelTest(TestCase):
    
    def setUp(self):
        """Configuración inicial para los tests de auditoría"""
        self.user = User.objects.create_user(
            username="admin",
            email="admin@example.com",
            cedula="99999999",
            password="admin123"
        )
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
        self.tasa = TasaDeCambio.objects.create(
            moneda_origen=self.moneda_usd,
            moneda_destino=self.moneda_pyg,
            precio_base=Decimal("7400.00"),
            comision_compra=Decimal("0.00"),
            comision_venta=Decimal("0.00"),
            vigencia=date.today(),
            estado=True
        )

    def test_crear_auditoria_creacion(self):
        """Verifica que se puede crear un registro de auditoría tipo CREACION"""
        auditoria = AuditoriaTasaCambio.objects.create(
            tasa=self.tasa,
            tipo_cambio='CREACION',
            precio_nuevo=Decimal("7400.00"),
            vigencia_nueva=date.today(),
            estado_nuevo=True,
            usuario_cambio=self.user
        )
        
        self.assertEqual(auditoria.tipo_cambio, 'CREACION')
        self.assertEqual(auditoria.precio_nuevo, Decimal("7400.00"))
        self.assertIsNone(auditoria.precio_anterior)
        self.assertEqual(auditoria.usuario_cambio, self.user)

    def test_crear_auditoria_edicion(self):
        """Verifica que se puede crear un registro de auditoría tipo EDICION"""
        auditoria = AuditoriaTasaCambio.objects.create(
            tasa=self.tasa,
            tipo_cambio='EDICION',
            precio_anterior=Decimal("7400.00"),
            precio_nuevo=Decimal("7500.00"),
            vigencia_anterior=date.today() - timedelta(days=1),
            vigencia_nueva=date.today(),
            estado_anterior=True,
            estado_nuevo=True,
            usuario_cambio=self.user
        )
        
        self.assertEqual(auditoria.tipo_cambio, 'EDICION')
        self.assertEqual(auditoria.precio_anterior, Decimal("7400.00"))
        self.assertEqual(auditoria.precio_nuevo, Decimal("7500.00"))

    def test_porcentaje_cambio(self):
        """Verifica el cálculo del porcentaje de cambio"""
        auditoria = AuditoriaTasaCambio.objects.create(
            tasa=self.tasa,
            tipo_cambio='EDICION',
            precio_anterior=Decimal("7000.00"),
            precio_nuevo=Decimal("7700.00"),
            vigencia_nueva=date.today(),
            estado_nuevo=True,
            usuario_cambio=self.user
        )
        
        # (7700 - 7000) / 7000 * 100 = 10%
        porcentaje = auditoria.porcentaje_cambio()
        self.assertEqual(porcentaje, 10)

    def test_porcentaje_cambio_sin_precio_anterior(self):
        """Verifica que el porcentaje es 0 cuando no hay precio anterior"""
        auditoria = AuditoriaTasaCambio.objects.create(
            tasa=self.tasa,
            tipo_cambio='CREACION',
            precio_nuevo=Decimal("7400.00"),
            vigencia_nueva=date.today(),
            estado_nuevo=True
        )
        
        self.assertEqual(auditoria.porcentaje_cambio(), 0)

    def test_str_method_auditoria(self):
        """Verifica el método __str__ de AuditoriaTasaCambio"""
        auditoria = AuditoriaTasaCambio.objects.create(
            tasa=self.tasa,
            tipo_cambio='CREACION',
            precio_nuevo=Decimal("7400.00"),
            vigencia_nueva=date.today(),
            estado_nuevo=True
        )
        
        expected = f"CREACION - {self.moneda_usd.abreviacion}"
        self.assertIn("CREACION", str(auditoria))
        self.assertIn(self.moneda_usd.abreviacion, str(auditoria))

    def test_ordering_fecha_cambio(self):
        """Verifica que las auditorías se ordenan por fecha descendente"""
        AuditoriaTasaCambio.objects.create(
            tasa=self.tasa,
            tipo_cambio='CREACION',
            precio_nuevo=Decimal("7400.00"),
            vigencia_nueva=date.today(),
            estado_nuevo=True
        )
        
        AuditoriaTasaCambio.objects.create(
            tasa=self.tasa,
            tipo_cambio='EDICION',
            precio_anterior=Decimal("7400.00"),
            precio_nuevo=Decimal("7500.00"),
            vigencia_nueva=date.today(),
            estado_nuevo=True
        )
        
        auditorias = AuditoriaTasaCambio.objects.all()
        self.assertEqual(auditorias[0].tipo_cambio, 'EDICION')
        self.assertEqual(auditorias[1].tipo_cambio, 'CREACION')