# limite_moneda/tests/test_forms.py
from django.test import TestCase
from decimal import Decimal, InvalidOperation
from clientes.models import Cliente, Segmentacion
from monedas.models import Moneda
from limite_moneda.forms import LimiteTransaccionForm

class LimiteTransaccionFormTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        # Crear segmentación de prueba
        cls.segmentacion = Segmentacion.objects.create(nombre="Segmento Test")
        
        # Crear cliente de prueba con segmentación
        cls.cliente = Cliente.objects.create(
            nombre="Cliente Test",
            estado="activo",
            segmentacion=cls.segmentacion
        )

        # Crear moneda de prueba
        cls.moneda = Moneda.objects.create(
            nombre="Guaraní",
            abreviacion="PYG",
            estado=True
        )

    def test_form_valido(self):
        """Formulario válido con límites correctos"""
        data = {
            'cliente': self.cliente.id,
            'moneda': self.moneda.id,
            'limite_diario': '100.50',
            'limite_mensual': '1000.75',
        }
        form = LimiteTransaccionForm(data=data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['limite_diario'], Decimal('100.50'))
        self.assertEqual(form.cleaned_data['limite_mensual'], Decimal('1000.75'))

    def test_limite_diario_negativo(self):
        data = {
            'cliente': self.cliente.id,
            'moneda': self.moneda.id,
            'limite_diario': '-10',
            'limite_mensual': '1000',
        }
        form = LimiteTransaccionForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('limite_diario', form.errors)
        self.assertEqual(form.errors['limite_diario'][0], "El límite diario debe ser mayor o igual a 0")

    def test_limite_mensual_negativo(self):
        data = {
            'cliente': self.cliente.id,
            'moneda': self.moneda.id,
            'limite_diario': '100',
            'limite_mensual': '-50',
        }
        form = LimiteTransaccionForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('limite_mensual', form.errors)
        self.assertEqual(form.errors['limite_mensual'][0], "El límite mensual debe ser mayor o igual a 0")

    def test_limite_mensual_menor_que_diario(self):
        data = {
            'cliente': self.cliente.id,
            'moneda': self.moneda.id,
            'limite_diario': '500',
            'limite_mensual': '100',
        }
        form = LimiteTransaccionForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('__all__', form.errors)
        self.assertEqual(form.errors['__all__'][0], "El límite mensual no puede ser menor al límite diario.")

    def test_campos_requeridos(self):
        form = LimiteTransaccionForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIn('cliente', form.errors)
        self.assertIn('moneda', form.errors)
        self.assertIn('limite_diario', form.errors)
        self.assertIn('limite_mensual', form.errors)


    def test_valor_invalido(self):
        """Se detecta valor no convertible a Decimal"""
        data = {
            'cliente': self.cliente.id,
            'moneda': self.moneda.id,
            'limite_diario': 'abc',
            'limite_mensual': '1000',
        }
        form = LimiteTransaccionForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('limite_diario', form.errors)
        # El mensaje ahora puede ser el default de DecimalField
        self.assertIn("Introduzca un número.", form.errors['limite_diario'][0])
