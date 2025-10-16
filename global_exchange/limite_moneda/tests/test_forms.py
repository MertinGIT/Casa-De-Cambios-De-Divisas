from django.test import TestCase
from decimal import Decimal
from monedas.models import Moneda
from limite_moneda.forms import LimiteTransaccionForm


class LimiteTransaccionFormTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.pyg = Moneda.objects.create(
            nombre="Guaraní",
            abreviacion="PYG",
            estado=True
        )

    def test_form_valido_con_datos_correctos(self):
        """Verifica que el formulario acepta datos válidos"""
        form = LimiteTransaccionForm(data={
            "limite_diario": "10000.50",
            "limite_mensual": "100000.00",
            "estado": "activo",
        })
        self.assertTrue(form.is_valid(), msg=form.errors)

    def test_form_rechaza_mensual_menor_que_diario(self):
        """Verifica que mensual >= diario"""
        form = LimiteTransaccionForm(data={
            "limite_diario": "100000.00",
            "limite_mensual": "10000.00",
            "estado": "activo",
        })
        self.assertFalse(form.is_valid())
        self.assertIn("__all__", form.errors)

    def test_form_rechaza_valores_negativos_diario(self):
        """Verifica que no acepta valores negativos en límite diario"""
        form = LimiteTransaccionForm(data={
            "limite_diario": "-1000.00",
            "limite_mensual": "10000.00",
            "estado": "activo",
        })
        self.assertFalse(form.is_valid())
        self.assertIn("limite_diario", form.errors)

    def test_form_rechaza_valores_negativos_mensual(self):
        """Verifica que no acepta valores negativos en límite mensual"""
        form = LimiteTransaccionForm(data={
            "limite_diario": "10000.00",
            "limite_mensual": "-50000.00",
            "estado": "activo",
        })
        self.assertFalse(form.is_valid())
        self.assertIn("limite_mensual", form.errors)

    def test_form_campos_requeridos(self):
        """Verifica que los campos obligatorios están presentes"""
        form = LimiteTransaccionForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIn("limite_diario", form.errors)
        self.assertIn("limite_mensual", form.errors)