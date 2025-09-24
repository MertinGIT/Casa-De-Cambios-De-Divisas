# operaciones/tests/test_models.py
from django.test import TestCase
from decimal import Decimal
from usuarios.models import CustomUser
from monedas.models import Moneda
from cotizaciones.models import TasaDeCambio
from operaciones.models import Transaccion
from django.utils import timezone

class TransaccionModelTest(TestCase):

    def setUp(self):
        # Crear usuario de prueba
        self.user = CustomUser.objects.create_user(
            username="usuario_test",
            password="test123",
            cedula="12345678"
        )

        # Crear monedas
        self.moneda_origen = Moneda.objects.create(nombre="Dólar", abreviacion="USD", estado=True)
        self.moneda_destino = Moneda.objects.create(nombre="Guaraní", abreviacion="PYG", estado=True)

        # Crear tasa de cambio
        self.tasa = TasaDeCambio.objects.create(
            moneda_origen=self.moneda_origen,
            moneda_destino=self.moneda_destino,
            monto_compra=Decimal("7000.0"),
            monto_venta=Decimal("7100.0"),
            estado=True,
            vigencia=timezone.now()
        )

    def test_crear_transaccion(self):
        """Se puede crear una transacción correctamente"""
        transaccion = Transaccion.objects.create(
            usuario=self.user,
            monto=Decimal("5000"),
            tipo="compra",
            estado="pendiente",
            moneda_origen=self.moneda_origen,
            moneda_destino=self.moneda_destino,
            tasa_usada=Decimal("7100.0"),
            tasa_ref=self.tasa
        )

        self.assertEqual(transaccion.usuario, self.user)
        self.assertEqual(transaccion.monto, Decimal("5000"))
        self.assertEqual(transaccion.tipo, "compra")
        self.assertEqual(transaccion.estado, "pendiente")
        self.assertEqual(transaccion.moneda_origen, self.moneda_origen)
        self.assertEqual(transaccion.moneda_destino, self.moneda_destino)
        self.assertEqual(transaccion.tasa_usada, Decimal("7100.0"))
        self.assertEqual(transaccion.tasa_ref, self.tasa)

    def test_str_method(self):
        """El método __str__ devuelve el string esperado"""
        transaccion = Transaccion.objects.create(
            usuario=self.user,
            monto=Decimal("1000"),
            tipo="venta",
            estado="confirmada",
            moneda_origen=self.moneda_origen,
            moneda_destino=self.moneda_destino,
            tasa_usada=Decimal("7100.0"),
            tasa_ref=self.tasa
        )

        expected_str = f"Transacción {transaccion.id} - VENTA 1000 {self.moneda_origen} -> {self.moneda_destino} [confirmada]"
        self.assertEqual(str(transaccion), expected_str)
