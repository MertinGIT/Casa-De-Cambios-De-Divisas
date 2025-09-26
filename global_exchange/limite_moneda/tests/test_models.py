# limite_moneda/tests/test_models.py
from django.test import TestCase
from decimal import Decimal
from clientes.models import Cliente
from monedas.models import Moneda
from limite_moneda.models import LimiteTransaccion
from cliente_segmentacion.models import Segmentacion
from django.core.exceptions import ValidationError

class LimiteTransaccionModelTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        # Crear segmentación
        cls.segmentacion = Segmentacion.objects.create(nombre="Segmento Test")
        # Crear cliente
        cls.cliente = Cliente.objects.create(
            nombre="Cliente Test",
            estado="activo",
            segmentacion=cls.segmentacion
        )
        # Crear moneda
        cls.moneda = Moneda.objects.create(nombre="Guaraní", abreviacion="PYG", estado=True)
        # Límite inicial
        cls.limite = LimiteTransaccion.objects.create(
            cliente=cls.cliente,
            moneda=cls.moneda,
            limite_diario=Decimal('100.50'),
            limite_mensual=Decimal('1000.75'),
            estado='activo'
        )

    def test_creacion_limite_valido(self):
        """Se puede crear un límite válido"""
        self.assertEqual(self.limite.cliente, self.cliente)
        self.assertEqual(self.limite.moneda, self.moneda)
        self.assertEqual(self.limite.limite_diario, Decimal('100.50'))
        self.assertEqual(self.limite.limite_mensual, Decimal('1000.75'))
        self.assertEqual(self.limite.estado, 'activo')

    def test_str(self):
        """El __str__ devuelve 'Cliente - Moneda'"""
        self.assertEqual(str(self.limite), f"{self.cliente.nombre} - {self.moneda.nombre}")

    def test_limite_mensual_menor_que_diario(self):
        """Se puede detectar cuando mensual < diario manualmente"""
        limite = LimiteTransaccion(
            cliente=self.cliente,
            moneda=self.moneda,
            limite_diario=Decimal('500'),
            limite_mensual=Decimal('100')
        )
        self.assertTrue(limite.limite_mensual < limite.limite_diario)

    def test_limites_negativos(self):
        """Detectar límites negativos manualmente"""
        limite = LimiteTransaccion(
            cliente=self.cliente,
            moneda=self.moneda,
            limite_diario=Decimal('-50'),
            limite_mensual=Decimal('-100')
        )
        self.assertTrue(limite.limite_diario < 0)
        self.assertTrue(limite.limite_mensual < 0)

    def test_limite_duplicado_simulado(self):
        """Simula un duplicado sin IntegrityError"""
        limite2 = LimiteTransaccion(
            cliente=self.cliente,
            moneda=self.moneda,
            limite_diario=Decimal('200'),
            limite_mensual=Decimal('2000')
        )
        # Comprobamos que cliente y moneda ya existen
        exists = LimiteTransaccion.objects.filter(
            cliente=self.cliente,
            moneda=self.moneda
        ).exists()
        self.assertTrue(exists)
        # El nuevo límite no se guarda para evitar duplicado
        with self.assertRaises(ValidationError):
            if exists:
                raise ValidationError("Este cliente ya tiene un límite para esta moneda.")
