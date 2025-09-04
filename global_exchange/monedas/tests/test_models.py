from django.test import TestCase
from monedas.models import Moneda

class MonedaModelTest(TestCase):
    def test_creacion_moneda(self):
        moneda = Moneda.objects.create(nombre='Dólar', abreviacion='USD')
        self.assertEqual(str(moneda), 'Dólar')
        self.assertTrue(moneda.estado)

    def test_estado_por_defecto(self):
        moneda = Moneda.objects.create(nombre='Euro', abreviacion='EUR')
        self.assertTrue(moneda.estado)
