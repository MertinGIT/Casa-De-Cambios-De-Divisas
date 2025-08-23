from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from decimal import Decimal
from django.utils import timezone
from clientes.models import Segmentacion, Cliente


class SegmentacionModelTest(TestCase):
    def setUp(self):
        self.segmentacion = Segmentacion.objects.create(
            nombre="Regular",
            descripcion="Cliente regular",
            descuento=10.00
        )

    def test_segmentacion_creation(self):
        self.assertEqual(self.segmentacion.nombre, "Regular")
        self.assertEqual(self.segmentacion.descripcion, "Cliente regular")
        self.assertEqual(self.segmentacion.descuento, Decimal('10.00'))

    def test_unique_nombre(self):
        with self.assertRaises(IntegrityError):
            Segmentacion.objects.create(nombre="Regular", descuento=5.00)

    def test_descuento_default(self):
        segmentacion = Segmentacion.objects.create(nombre="VIP")
        self.assertEqual(segmentacion.descuento, Decimal('0.00'))

class ClienteModelTest(TestCase):
    def setUp(self):
        self.segmentacion = Segmentacion.objects.create(
            nombre="Regular",
            descripcion="Cliente regular",
            descuento=10.50
        )
        self.cliente = Cliente.objects.create(
            nombre="John Doe",
            email="martin@gmail.com",
            telefono="1234567890",
            segmentacion=self.segmentacion,
            estado='activo'
        )

    def test_cliente_creation(self):
        self.assertEqual(self.cliente.nombre, "John Doe")
        self.assertEqual(self.cliente.email, "martin@gmail.com")
        self.assertEqual(self.cliente.telefono, "1234567890")
        self.assertEqual(self.cliente.segmentacion, self.segmentacion)
        self.assertEqual(self.cliente.estado, 'activo')

    def test_email_unique(self):
        with self.assertRaises(IntegrityError):
            Cliente.objects.create(
                nombre="Jane Doe",
                email="martin@gmail.com",
                telefono="0987654321",
                segmentacion=self.segmentacion,
                estado='activo'
            )
    def test_estado_default(self):
        cliente = Cliente.objects.create(
            nombre="Alice Smith",
            email="alice@gmail.com",
            segmentacion=self.segmentacion,
            telefono="5551234567",
            estado='Activo'
        )
        self.assertEqual(cliente.estado, 'activo')
    