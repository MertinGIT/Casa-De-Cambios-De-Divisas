from django.test import TestCase
from decimal import Decimal
from tauser.models import Localidad, Denominacion, StockTauser
from monedas.models import Moneda


class LocalidadModelTest(TestCase):
    """Tests para el modelo Localidad"""

    def setUp(self):
        self.localidad = Localidad.objects.create(
            nombre="Sucursal Central",
            direccion="Av. Mariscal López 1234",
            activo=True
        )

    def test_crear_localidad(self):
        """Test: Crear una localidad correctamente"""
        self.assertEqual(self.localidad.nombre, "Sucursal Central")
        self.assertTrue(self.localidad.activo)

    def test_str_localidad(self):
        """Test: Representación en string"""
        self.assertEqual(str(self.localidad), "Sucursal Central")


class DenominacionModelTest(TestCase):
    """Tests para el modelo Denominacion"""

    def setUp(self):
        # ✅ Moneda solo tiene: nombre, abreviacion, estado
        self.moneda = Moneda.objects.create(
            nombre="Guaraní",
            abreviacion="PYG",
            estado=True
        )
        self.denominacion = Denominacion.objects.create(
            moneda=self.moneda,
            valor=Decimal("100000.00"),
            activo=True
        )

    def test_crear_denominacion(self):
        """Test: Crear denominación correctamente"""
        self.assertEqual(self.denominacion.valor, Decimal("100000.00"))
        self.assertTrue(self.denominacion.activo)

    def test_str_denominacion(self):
        """Test: Representación en string"""
        self.assertEqual(str(self.denominacion), "PYG 100000.00")


class StockTauserModelTest(TestCase):
    """Tests para el modelo StockTauser"""

    def setUp(self):
        self.localidad = Localidad.objects.create(
            nombre="Sucursal Test",
            direccion="Test",
            activo=True
        )
        # ✅ Moneda con campos correctos
        self.moneda = Moneda.objects.create(
            nombre="Guaraní",
            abreviacion="PYG",
            estado=True
        )
        self.denominacion = Denominacion.objects.create(
            moneda=self.moneda,
            valor=Decimal("100000.00"),
            activo=True
        )
        self.stock = StockTauser.objects.create(
            localidad=self.localidad,
            denominacion=self.denominacion,
            cantidad=50,
            cantidad_minima=10
        )

    def test_crear_stock(self):
        """Test: Crear stock correctamente"""
        self.assertEqual(self.stock.cantidad, 50)
        self.assertEqual(self.stock.cantidad_minima, 10)

    def test_valor_total(self):
        """Test: Calcular valor total del stock"""
        valor_total = self.stock.valor_total
        self.assertEqual(valor_total, Decimal("5000000.00"))

    def test_stock_bajo(self):
        """Test: Verificar stock bajo"""
        self.assertFalse(self.stock.stock_bajo)
        
        self.stock.cantidad = 5
        self.stock.save()
        self.assertTrue(self.stock.stock_bajo)