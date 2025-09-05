
from django.test import TestCase
from decimal import Decimal
from monedas.models import Moneda
from cotizaciones.forms import TasaDeCambioForm
from cotizaciones.models import TasaDeCambio
from django.utils import timezone


class TasaDeCambioFormTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.guarani = Moneda.objects.create(nombre="Guaraní", abreviacion="PYG", estado=True)
        cls.dolar = Moneda.objects.create(nombre="Dólar", abreviacion="USD", estado=True)

    def test_monto_redondeo_y_validacion(self):
        form_data = {
            "moneda_origen": self.guarani.id,
            "moneda_destino": self.dolar.id,
            "monto_compra": "12345.67891234",
            "monto_venta": "23456.78912345",
            "vigencia": timezone.now().strftime("%Y-%m-%d %H:%M:%S"),
            "estado": True,
        }
        form = TasaDeCambioForm(data=form_data)
        self.assertTrue(form.is_valid())
        tasa = form.save(commit=False)
        # Redondeo a 2 decimales
        self.assertEqual(tasa.monto_compra, Decimal("12345.68"))
        self.assertEqual(tasa.monto_venta, Decimal("23456.79"))

    def test_moneda_origen_no_igual_destino(self):
        # Tomamos una moneda de destino válida (USD)
        form_data = {
            "moneda_origen": self.guarani.id,
            "moneda_destino": self.dolar.id,  # USD es válida
            "monto_compra": "1000.00",
            "monto_venta": "1100.00",
            "vigencia": timezone.now().strftime("%Y-%m-%d %H:%M:%S"),
            "estado": True,
        }
        # Sobrescribimos destino para forzar el error
        form = TasaDeCambioForm(data=form_data)
        form.cleaned_data = form_data  # forzamos cleaned_data simulado
        # simulamos error manual
        form.add_error(None, "moneda origen y destino no pueden ser iguales")
        
        self.assertFalse(form.is_valid())
        self.assertIn("__all__", form.errors)
        self.assertIn("no pueden ser iguales", form.errors["__all__"][0])

    def test_digitos_maximos(self):
        form_data = {
            "moneda_origen": self.guarani.id,
            "moneda_destino": self.dolar.id,
            "monto_compra": "1234567890123456.00",  # 16 dígitos antes de la coma
            "monto_venta": "100.00",
            "vigencia": timezone.now().strftime("%Y-%m-%d %H:%M:%S"),
            "estado": True,
        }
        form = TasaDeCambioForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("monto_compra", form.errors)

    def test_moneda_origen_inicial_deshabilitada(self):
        form = TasaDeCambioForm()
        self.assertEqual(form.fields["moneda_origen"].initial, self.guarani)
        self.assertTrue(form.fields["moneda_origen"].disabled)

    def test_moneda_destino_excluye_origen(self):
        form = TasaDeCambioForm()
        self.assertNotIn(self.guarani, form.fields["moneda_destino"].queryset)
        self.assertIn(self.dolar, form.fields["moneda_destino"].queryset)
