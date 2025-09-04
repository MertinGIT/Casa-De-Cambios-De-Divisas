"""
Pruebas unitarias para modelo MetodoPago
"""

from django.test import TestCase
from django.db import IntegrityError
from metodos_pagos.models import MetodoPago


class MetodoPagoModelTest(TestCase):
    
    def test_create_metodo_pago(self):
        """Test creación básica de método de pago"""
        metodo = MetodoPago.objects.create(
            nombre='PayPal',
            descripcion='Pago online'
        )
        self.assertEqual(metodo.nombre, 'PayPal')
        self.assertEqual(metodo.descripcion, 'Pago online')
        self.assertFalse(metodo.activo)  # Default False

    def test_str_representation(self):
        """Test representación string del modelo"""
        metodo = MetodoPago.objects.create(nombre='Efectivo')
        self.assertEqual(str(metodo), 'Efectivo')

    def test_nombre_unique_constraint(self):
        """Test restricción de unicidad en nombre"""
        MetodoPago.objects.create(nombre='Bitcoin')
        with self.assertRaises(IntegrityError):
            MetodoPago.objects.create(nombre='Bitcoin')

    def test_default_values(self):
        """Test valores por defecto"""
        metodo = MetodoPago.objects.create(nombre='Test')
        self.assertFalse(metodo.activo)
        self.assertIsNone(metodo.descripcion)

    def test_activo_toggle(self):
        """Test cambio de estado activo"""
        metodo = MetodoPago.objects.create(nombre='Zelle')
        self.assertFalse(metodo.activo)
        
        metodo.activo = True
        metodo.save()
        metodo.refresh_from_db()
        self.assertTrue(metodo.activo)

    def test_ordering(self):
        """Test ordenamiento por nombre"""
        MetodoPago.objects.create(nombre='Zelle')
        MetodoPago.objects.create(nombre='Bitcoin')
        MetodoPago.objects.create(nombre='Efectivo')
        
        nombres = list(MetodoPago.objects.values_list('nombre', flat=True))
        self.assertEqual(nombres, ['Bitcoin', 'Efectivo', 'Zelle'])

    def test_filter_operations(self):
        """Test operaciones de filtrado"""
        MetodoPago.objects.create(nombre='Tarjeta Visa', activo=True)
        MetodoPago.objects.create(nombre='Tarjeta Master', activo=False)
        MetodoPago.objects.create(nombre='PayPal', activo=True)
        
        activos = MetodoPago.objects.filter(activo=True)
        self.assertEqual(activos.count(), 2)
        
        tarjetas = MetodoPago.objects.filter(nombre__icontains='Tarjeta')
        self.assertEqual(tarjetas.count(), 2)
        nombres = ['PayPal (Online)', 'Visa/Mastercard', 'Bitcoin - BTC', '  Zelle @ USA  ']
        for n in nombres:
            obj = MetodoPago.objects.create(nombre=n)
            self.assertEqual(obj.nombre, n)
