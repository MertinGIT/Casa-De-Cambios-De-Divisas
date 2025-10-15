# limite_moneda/tests/test_models.py
from decimal import Decimal
from django.test import TestCase
from limite_moneda.models import LimiteTransaccion

class LimiteTransaccionModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.limite = LimiteTransaccion.objects.create(
            # cliente eliminado
            limite_diario=Decimal("1000000.00"),
            limite_mensual=Decimal("10000000.00"),
            estado="activo",
        )

    def test_str(self):
        s = str(self.limite)
        self.assertIn("Límites", s)
        self.assertIn("Diario", s)
        self.assertIn("Mensual", s)
