# limite_moneda/tests/test_forms.py
from django.test import TestCase
from limite_moneda.forms import LimiteTransaccionForm

class LimiteTransaccionFormTest(TestCase):
    def test_campos_requeridos(self):
        form = LimiteTransaccionForm(data={})
        # cliente eliminado; validar límites requeridos
        self.assertIn('limite_diario', form.errors)
        self.assertIn('limite_mensual', form.errors)

    def test_form_valido(self):
        form = LimiteTransaccionForm(data={
            # 'cliente': <eliminado>,
            'limite_diario': '1000000.00',
            'limite_mensual': '5000000.00',
            'estado': 'activo',
        })
        self.assertTrue(form.is_valid(), msg=form.errors)
