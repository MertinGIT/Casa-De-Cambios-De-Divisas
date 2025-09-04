from django.test import TestCase
from django.db import IntegrityError
from decimal import Decimal
from cliente_segmentacion.models import Segmentacion


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
        self.assertEqual(self.segmentacion.descuento, Decimal("10.00"))

    def test_unique_nombre(self):
        with self.assertRaises(IntegrityError):
            Segmentacion.objects.create(nombre="Regular", descuento=5.00)

    def test_descuento_default(self):
        segmentacion = Segmentacion.objects.create(nombre="VIP")
        self.assertEqual(segmentacion.descuento, Decimal("0.00"))
