# operaciones/tests/test_models.py
from django.test import TestCase
from decimal import Decimal
from usuarios.models import CustomUser
from monedas.models import Moneda
from cotizaciones.models import TasaDeCambio
from operaciones.models import Transaccion
from clientes.models import Cliente
from cliente_segmentacion.models import Segmentacion
from metodos_pagos.models import MetodoPago  # ← AGREGAR IMPORT
from django.utils import timezone

class TransaccionModelTest(TestCase):

    def setUp(self):
        # Crear usuario de prueba
        self.user = CustomUser.objects.create_user(
            username="usuario_test",
            password="test123",
            cedula="12345678"
        )

        # Crear segmentación y cliente
        self.segmentacion = Segmentacion.objects.create(
            nombre="Segmento Test",
            estado="activo",
            descuento=10
        )
        self.cliente = Cliente.objects.create(
            nombre="Cliente Test",
            segmentacion=self.segmentacion,
            email="cliente@test.com",
            estado="activo"
        )

        # Crear monedas
        self.moneda_origen = Moneda.objects.create(nombre="Dólar", abreviacion="USD", estado=True)
        self.moneda_destino = Moneda.objects.create(nombre="Guaraní", abreviacion="PYG", estado=True)

        # Crear tasa de cambio
        self.tasa = TasaDeCambio.objects.create(
            moneda_origen=self.moneda_origen,
            moneda_destino=self.moneda_destino,
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

    def test_crear_transaccion(self):
        """Se puede crear una transacción correctamente"""
        transaccion = Transaccion.objects.create(
            usuario=self.user,
            cliente=self.cliente,
            monto=Decimal("5000"),
            tipo="compra",
            estado="pendiente",
            moneda_origen=self.moneda_origen,
            moneda_destino=self.moneda_destino,
            tasa_usada=Decimal("7100.0"),
            tasa_ref=self.tasa,
            metodo_pago=self.metodo_pago  # ← AGREGAR ESTE CAMPO
        )

        self.assertEqual(transaccion.usuario, self.user)
        self.assertEqual(transaccion.cliente, self.cliente)
        self.assertEqual(transaccion.monto, Decimal("5000"))
        self.assertEqual(transaccion.tipo, "compra")
        self.assertEqual(transaccion.estado, "pendiente")
        self.assertEqual(transaccion.moneda_origen, self.moneda_origen)
        self.assertEqual(transaccion.moneda_destino, self.moneda_destino)
        self.assertEqual(transaccion.tasa_usada, Decimal("7100.0"))
        self.assertEqual(transaccion.tasa_ref, self.tasa)
        self.assertEqual(transaccion.metodo_pago, self.metodo_pago)  # ← VERIFICAR

    def test_str_method(self):
        """El método __str__ devuelve el string esperado"""
        transaccion = Transaccion.objects.create(
            usuario=self.user,
            cliente=self.cliente,
            monto=Decimal("1000"),
            tipo="venta",
            estado="confirmada",
            moneda_origen=self.moneda_origen,
            moneda_destino=self.moneda_destino,
            tasa_usada=Decimal("7100.0"),
            tasa_ref=self.tasa,
            metodo_pago=self.metodo_pago  # ← AGREGAR ESTE CAMPO
        )

        expected_str = f"Transacción {transaccion.id} - VENTA 1000 {self.moneda_origen} -> {self.moneda_destino} [confirmada]"
        self.assertEqual(str(transaccion), expected_str)
