"""
Pruebas unitarias para formularios de métodos de pago
"""

from django.test import TestCase
from metodos_pagos.forms import MetodoPagoForm
from metodos_pagos.models import MetodoPago


class MetodoPagoFormTest(TestCase):
    
    def test_form_valid_data(self):
        """Test formulario con datos válidos"""
        form = MetodoPagoForm(data={
            'nombre': 'PayPal',
            'descripcion': 'Pago online'
        })
        self.assertTrue(form.is_valid())
        obj = form.save()
        self.assertEqual(obj.nombre, 'PayPal')
        self.assertEqual(obj.descripcion, 'Pago online')

    def test_nombre_required(self):
        """Test nombre es obligatorio"""
        form = MetodoPagoForm(data={'descripcion': 'Test'})
        self.assertFalse(form.is_valid())
        self.assertIn('nombre', form.errors)

    def test_nombre_empty_spaces(self):
        """Test nombre con solo espacios"""
        form = MetodoPagoForm(data={'nombre': '   ', 'descripcion': 'Test'})
        self.assertFalse(form.is_valid())
        self.assertIn('nombre', form.errors)

    def test_nombre_min_length(self):
        """Test longitud mínima de nombre"""
        form = MetodoPagoForm(data={'nombre': 'ab'})
        self.assertFalse(form.is_valid())
        self.assertIn('nombre', form.errors)

    def test_nombre_max_length(self):
        """Test longitud máxima de nombre"""
        form = MetodoPagoForm(data={'nombre': 'a' * 101})
        self.assertFalse(form.is_valid())
        self.assertIn('nombre', form.errors)

    def test_nombre_unique(self):
        """Test unicidad de nombre"""
        MetodoPago.objects.create(nombre='PayPal')
        form = MetodoPagoForm(data={'nombre': 'paypal'})
        self.assertFalse(form.is_valid())
        self.assertIn('nombre', form.errors)

    def test_descripcion_default(self):
        """Test descripción por defecto cuando está vacía"""
        form = MetodoPagoForm(data={'nombre': 'Efectivo', 'descripcion': ''})
        self.assertTrue(form.is_valid())
        obj = form.save()
        self.assertEqual(obj.descripcion, 'No hay descripción')

    def test_descripcion_max_length(self):
        """Test longitud máxima de descripción"""
        form = MetodoPagoForm(data={
            'nombre': 'Test',
            'descripcion': 'x' * 501
        })
        self.assertFalse(form.is_valid())
        self.assertIn('descripcion', form.errors)

    def test_form_update_existing(self):
        """Test actualización de objeto existente"""
        metodo = MetodoPago.objects.create(nombre='Original')
        form = MetodoPagoForm(
            data={'nombre': 'Actualizado', 'descripcion': 'Nueva desc'},
            instance=metodo
        )
        self.assertTrue(form.is_valid())
        updated = form.save()
        self.assertEqual(updated.pk, metodo.pk)
        self.assertEqual(updated.nombre, 'Actualizado')

    def test_form_fields_configuration(self):
        """Test configuración de campos del formulario"""
        form = MetodoPagoForm()
        self.assertTrue(form.fields['nombre'].required)
        self.assertFalse(form.fields['descripcion'].required)
        
        # Test widgets
        nombre_widget = form.fields['nombre'].widget
        desc_widget = form.fields['descripcion'].widget
        
        self.assertEqual(nombre_widget.attrs.get('class'), 'form-control custom-input')
        self.assertEqual(desc_widget.attrs.get('class'), 'form-control custom-input')
