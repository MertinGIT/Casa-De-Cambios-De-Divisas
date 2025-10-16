from django.test import TestCase
from decimal import Decimal
from monedas.models import Moneda
from limite_moneda.models import LimiteTransaccion


class LimiteTransaccionModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Crear moneda PYG (requerida por el modelo)
        cls.pyg = Moneda.objects.create(
            nombre="Guaraní",
            abreviacion="PYG",
            estado=True
        )

    def test_crear_limite_con_valores_validos(self):
        """Verifica creación de límite con datos válidos"""
        limite = LimiteTransaccion.objects.create(
            limite_diario=Decimal("10000.00"),
            limite_mensual=Decimal("100000.00"),
            estado="activo"
        )
        self.assertEqual(limite.limite_diario, Decimal("10000.00"))
        self.assertEqual(limite.limite_mensual, Decimal("100000.00"))
        self.assertEqual(limite.estado, "activo")
        self.assertEqual(limite.moneda, self.pyg)

    def test_moneda_default_es_pyg(self):
        """Verifica que la moneda por defecto es PYG"""
        limite = LimiteTransaccion.objects.create(
            limite_diario=Decimal("5000.00"),
            limite_mensual=Decimal("50000.00")
        )
        self.assertEqual(limite.moneda.abreviacion, "PYG")

    def test_estado_default_es_activo(self):
        """Verifica que el estado por defecto es activo"""
        limite = LimiteTransaccion.objects.create(
            limite_diario=Decimal("5000.00"),
            limite_mensual=Decimal("50000.00")
        )
        self.assertEqual(limite.estado, "activo")

    def test_str_representation(self):
        """Verifica la representación en string"""
        limite = LimiteTransaccion.objects.create(
            limite_diario=Decimal("5000"),
            limite_mensual=Decimal("50000")
        )
        expected = "Límites (Diario: 5000, Mensual: 50000)"
        self.assertEqual(str(limite), expected)