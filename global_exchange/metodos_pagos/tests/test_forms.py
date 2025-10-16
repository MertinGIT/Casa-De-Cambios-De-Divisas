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

    def test_nombre_required(self):
        """Test campo nombre es obligatorio"""
        form = MetodoPagoForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIn('nombre', form.errors)

    def test_nombre_empty_spaces(self):
        """Test nombre con solo espacios es inválido"""
        form = MetodoPagoForm(data={'nombre': '   '})
        self.assertFalse(form.is_valid())
        self.assertIn('nombre', form.errors)

    def test_nombre_min_length(self):
        """Test longitud mínima de nombre (3 caracteres)"""
        form = MetodoPagoForm(data={'nombre': 'ab'})
        self.assertFalse(form.is_valid())
        self.assertIn('nombre', form.errors)

    def test_nombre_max_length(self):
        """Test longitud máxima de nombre (100 caracteres)"""
        form = MetodoPagoForm(data={'nombre': 'x' * 101})
        self.assertFalse(form.is_valid())
        self.assertIn('nombre', form.errors)

    def test_nombre_unique(self):
        """Test unicidad de nombre"""
        MetodoPago.objects.create(nombre='Efectivo Unique Test')
        form = MetodoPagoForm(data={'nombre': 'Efectivo Unique Test'})
        self.assertFalse(form.is_valid())
        self.assertIn('nombre', form.errors)

    def test_descripcion_default(self):
        """Test descripción por defecto cuando está vacía"""
        # ← CORREGIR: Enviar nombre válido y descripción vacía
        form = MetodoPagoForm(data={
            'nombre': 'Tarjeta de Crédito Test',
            'descripcion': ''  # Explícitamente vacío
        })
        self.assertTrue(form.is_valid())
        # Verificar que se aplicó el default
        self.assertEqual(form.cleaned_data['descripcion'], 'No hay descripción')

    def test_descripcion_max_length(self):
        """Test longitud máxima de descripción (500 caracteres)"""
        form = MetodoPagoForm(data={
            'nombre': 'Bitcoin Test',
            'descripcion': 'x' * 501
        })
        self.assertFalse(form.is_valid())
        self.assertIn('descripcion', form.errors)

    def test_form_update_existing(self):
        """Test actualización de método existente"""
        metodo = MetodoPago.objects.create(
            nombre='Zelle Update Test',
            descripcion='Pago digital'
        )
        form = MetodoPagoForm(
            instance=metodo,
            data={'nombre': 'Zelle Update Test', 'descripcion': 'Pago digital actualizado'}
        )
        self.assertTrue(form.is_valid())
        updated = form.save()
        self.assertEqual(updated.descripcion, 'Pago digital actualizado')

    def test_form_fields_configuration(self):
        """Test configuración de campos del formulario"""
        form = MetodoPagoForm()
        # Verificar que los campos esperados están presentes
        self.assertIn('nombre', form.fields)
        self.assertIn('descripcion', form.fields)
        # Verificar requerimientos
        self.assertTrue(form.fields['nombre'].required)
        self.assertFalse(form.fields['descripcion'].required)
