# tests/test_forms.py
from django.test import TestCase
from cliente_segmentacion.forms import SegmentacionForm


class SegmentacionFormTests(TestCase):

    def test_form_valido(self):
        form_data = {
            "nombre": "VIP",
            "descripcion": "Clientes preferenciales",
            "descuento": 20,
            "estado": "activo"
        }
        form = SegmentacionForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_descuento_negativo(self):
        form_data = {
            "nombre": "VIP",
            "descripcion": "Clientes preferenciales",
            "descuento": -5,
            "estado": "activo"
        }
        form = SegmentacionForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("El descuento no puede ser negativo.", form.errors["descuento"])

    def test_descuento_mayor_100(self):
        form_data = {
            "nombre": "VIP",
            "descripcion": "Clientes preferenciales",
            "descuento": 150,
            "estado": "activo"
        }
        form = SegmentacionForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("El descuento no puede ser mayor a 100%.", form.errors["descuento"])

    def test_estado_por_defecto(self):
        form = SegmentacionForm()
        self.assertEqual(form.fields["estado"].initial, "activo")
