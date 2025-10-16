from django.test import TestCase
from django.utils import timezone
from decimal import Decimal
from monedas.models import Moneda
from cotizaciones.models import TasaDeCambio


class TasaDeCambioModelTest(TestCase):
    """Tests para el modelo TasaDeCambio"""
    
    @classmethod
    def setUpTestData(cls):
        """Configuración inicial de datos de prueba"""
        cls.guarani = Moneda.objects.create(
            nombre="Guaraní",
            abreviacion="PYG",
            estado=True
        )
        cls.dolar = Moneda.objects.create(
            nombre="Dólar",
            abreviacion="USD",
            estado=True
        )
        cls.euro = Moneda.objects.create(
            nombre="Euro",
            abreviacion="EUR",
            estado=True
        )

    def test_crear_tasa_cambio(self):
        """Verifica que se puede crear una tasa de cambio correctamente"""
        tasa = TasaDeCambio.objects.create(
            moneda_origen=self.guarani,
            moneda_destino=self.dolar,
            precio_base=Decimal("7400.00"),
            comision_compra=Decimal("10.00"),
            comision_venta=Decimal("15.00"),
            vigencia=timezone.now(),
            estado=True
        )
        self.assertEqual(tasa.moneda_origen, self.guarani)
        self.assertEqual(tasa.moneda_destino, self.dolar)
        self.assertEqual(tasa.precio_base, Decimal("7400.00"))
        self.assertTrue(tasa.estado)

    def test_monto_compra_property(self):
        """Verifica que monto_compra se calcula correctamente"""
        tasa = TasaDeCambio.objects.create(
            moneda_origen=self.guarani,
            moneda_destino=self.dolar,
            precio_base=Decimal("7400.00"),
            comision_compra=Decimal("10.00"),
            comision_venta=Decimal("0.00"),
            vigencia=timezone.now(),
            estado=True
        )
        # monto_compra = precio_base - comision_compra = 7400 - 10 = 7390
        self.assertEqual(tasa.monto_compra, Decimal("7390.00"))

    def test_monto_venta_property(self):
        """Verifica que monto_venta se calcula correctamente"""
        tasa = TasaDeCambio.objects.create(
            moneda_origen=self.guarani,
            moneda_destino=self.euro,
            precio_base=Decimal("8000.00"),
            comision_compra=Decimal("0.00"),
            comision_venta=Decimal("20.00"),
            vigencia=timezone.now(),
            estado=True
        )
        # monto_venta = precio_base + comision_venta = 8000 + 20 = 8020
        self.assertEqual(tasa.monto_venta, Decimal("8020.00"))

    def test_str_representation(self):
        """Verifica la representación en string de la tasa"""
        tasa = TasaDeCambio.objects.create(
            moneda_origen=self.guarani,
            moneda_destino=self.dolar,
            precio_base=Decimal("7400.00"),
            comision_compra=Decimal("5.00"),
            comision_venta=Decimal("10.00"),
            vigencia=timezone.now(),
            estado=True
        )
        expected = "Guaraní/Dólar - Precio: 7400.00 (+10.00/-5.00)"
        self.assertEqual(str(tasa), expected)

    def test_vigencia_default(self):
        """Verifica que vigencia tiene un valor por defecto"""
        tasa = TasaDeCambio.objects.create(
            moneda_origen=self.guarani,
            moneda_destino=self.dolar,
            precio_base=Decimal("7400.00"),
            comision_compra=Decimal("0.00"),
            comision_venta=Decimal("0.00"),
            estado=True
        )
        self.assertIsNotNone(tasa.vigencia)

    def test_estado_default_true(self):
        """Verifica que el estado por defecto es True"""
        tasa = TasaDeCambio.objects.create(
            moneda_origen=self.guarani,
            moneda_destino=self.dolar,
            precio_base=Decimal("7400.00"),
            comision_compra=Decimal("0.00"),
            comision_venta=Decimal("0.00"),
            vigencia=timezone.now()
        )
        self.assertTrue(tasa.estado)

    def test_monto_compra_no_negativo(self):
        """Verifica que monto_compra no devuelve valores negativos"""
        tasa = TasaDeCambio.objects.create(
            moneda_origen=self.guarani,
            moneda_destino=self.dolar,
            precio_base=Decimal("100.00"),
            comision_compra=Decimal("200.00"),  # comisión mayor que precio_base
            comision_venta=Decimal("0.00"),
            vigencia=timezone.now(),
            estado=True
        )
        # monto_compra no debe ser negativo
        self.assertEqual(tasa.monto_compra, Decimal("0.00"))