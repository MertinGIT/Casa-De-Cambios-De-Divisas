from django.test import TestCase
from django.utils import timezone
from decimal import Decimal
from monedas.models import Moneda
from cotizaciones.forms import TasaDeCambioForm


class TasaDeCambioFormTest(TestCase):
    """Tests para el formulario TasaDeCambioForm"""
    
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

    def test_form_valido_datos_completos(self):
        """Verifica que el formulario es válido con datos completos"""
        form_data = {
            "moneda_origen": self.guarani.id,
            "moneda_destino": self.dolar.id,
            "precio_base": "7400.50",
            "comision_compra": "10.00",
            "comision_venta": "15.00",
            "vigencia": timezone.now().strftime("%d/%m/%Y %H:%M"),
            "estado": True,
        }
        form = TasaDeCambioForm(data=form_data)
        self.assertTrue(form.is_valid(), msg=form.errors)

    def test_form_valido_sin_comisiones(self):
        """Verifica que el formulario es válido sin comisiones (opcionales)"""
        form_data = {
            "moneda_origen": self.guarani.id,
            "moneda_destino": self.dolar.id,
            "precio_base": "7400.00",
            "vigencia": timezone.now().strftime("%d/%m/%Y %H:%M"),
            "estado": True,
        }
        form = TasaDeCambioForm(data=form_data)
        self.assertTrue(form.is_valid(), msg=form.errors)

    def test_form_valido_sin_vigencia(self):
        """Verifica que vigencia es opcional y se asigna timezone.now()"""
        form_data = {
            "moneda_origen": self.guarani.id,
            "moneda_destino": self.euro.id,
            "precio_base": "8500.00",
            "comision_compra": "0.00",
            "comision_venta": "0.00",
            "estado": True,
        }
        form = TasaDeCambioForm(data=form_data)
        self.assertTrue(form.is_valid(), msg=form.errors)
        tasa = form.save()
        self.assertIsNotNone(tasa.vigencia)

    def test_precio_base_requerido(self):
        """Verifica que precio_base es obligatorio"""
        form_data = {
            "moneda_origen": self.guarani.id,
            "moneda_destino": self.dolar.id,
            "comision_compra": "0.00",
            "comision_venta": "0.00",
            "estado": True,
        }
        form = TasaDeCambioForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("precio_base", form.errors)

    def test_moneda_origen_igual_destino_invalido(self):
        """Verifica que Guaraní no puede ser moneda destino (está excluida)"""
        form = TasaDeCambioForm()
        # Verificar que Guaraní NO está en las opciones de moneda_destino
        self.assertNotIn(self.guarani, form.fields["moneda_destino"].queryset)

    def test_moneda_origen_inicial_guarani(self):
        """Verifica que moneda_origen se inicializa con Guaraní"""
        form = TasaDeCambioForm()
        self.assertEqual(form.fields["moneda_origen"].initial, self.guarani)

    def test_moneda_origen_deshabilitada(self):
        """Verifica que el campo moneda_origen está deshabilitado"""
        form = TasaDeCambioForm()
        self.assertTrue(form.fields["moneda_origen"].disabled)

    def test_moneda_destino_excluye_guarani(self):
        """Verifica que Guaraní no aparece en las opciones de moneda_destino"""
        form = TasaDeCambioForm()
        monedas_destino = list(form.fields["moneda_destino"].queryset)
        self.assertNotIn(self.guarani, monedas_destino)
        self.assertIn(self.dolar, monedas_destino)
        self.assertIn(self.euro, monedas_destino)

    def test_formato_vigencia_dd_mm_yyyy(self):
        """Verifica que acepta el formato dd/mm/yyyy HH:MM"""
        form_data = {
            "moneda_origen": self.guarani.id,
            "moneda_destino": self.dolar.id,
            "precio_base": "7400.00",
            "vigencia": "15/10/2025 14:30",
            "estado": True,
        }
        form = TasaDeCambioForm(data=form_data)
        self.assertTrue(form.is_valid(), msg=form.errors)

    def test_formato_vigencia_yyyy_mm_dd(self):
        """Verifica que acepta el formato yyyy-mm-dd HH:MM"""
        form_data = {
            "moneda_origen": self.guarani.id,
            "moneda_destino": self.dolar.id,
            "precio_base": "7400.00",
            "vigencia": "2025-10-15 14:30",
            "estado": True,
        }
        form = TasaDeCambioForm(data=form_data)
        self.assertTrue(form.is_valid(), msg=form.errors)