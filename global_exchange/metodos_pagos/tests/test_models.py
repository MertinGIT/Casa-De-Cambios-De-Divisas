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
        self.assertTrue(metodo.activo)  # Default True

    def test_str_representation(self):
        """Test representación string del modelo"""
        # ← CAMBIAR: Usar get_or_create o nombre único
        metodo, created = MetodoPago.objects.get_or_create(
            nombre='Efectivo Test STR',
            defaults={'descripcion': 'Test para __str__'}
        )
        self.assertEqual(str(metodo), 'Efectivo Test STR')

    def test_nombre_unique_constraint(self):
        """Test restricción de unicidad en nombre"""
        MetodoPago.objects.create(nombre='Bitcoin')
        with self.assertRaises(IntegrityError):
            MetodoPago.objects.create(nombre='Bitcoin')

    def test_default_values(self):
        """Test valores por defecto"""
        metodo = MetodoPago.objects.create(nombre='Test Default Values')
        self.assertTrue(metodo.activo)  # Default True
        self.assertIsNone(metodo.descripcion)

    def test_activo_toggle(self):
        """Test cambio de estado activo"""
        metodo = MetodoPago.objects.create(nombre='Zelle Test')
        self.assertTrue(metodo.activo)  # Default True

        metodo.activo = False
        metodo.save()
        metodo.refresh_from_db()
        self.assertFalse(metodo.activo)

    def test_ordering(self):
        """Test ordenamiento por nombre"""
        # ← LIMPIAR TABLA PRIMERO para evitar conflictos con datos precargados
        MetodoPago.objects.all().delete()
        
        MetodoPago.objects.create(nombre='Zelle Ordering')
        MetodoPago.objects.create(nombre='Bitcoin Ordering')
        MetodoPago.objects.create(nombre='Efectivo Ordering')

        nombres = list(MetodoPago.objects.values_list('nombre', flat=True))
        self.assertEqual(nombres, ['Bitcoin Ordering', 'Efectivo Ordering', 'Zelle Ordering'])

    def test_filter_operations(self):
        """Test operaciones de filtrado"""
        # ← LIMPIAR TABLA PRIMERO
        MetodoPago.objects.all().delete()
        
        MetodoPago.objects.create(nombre='Tarjeta Visa', activo=True)
        MetodoPago.objects.create(nombre='Tarjeta Master', activo=False)
        MetodoPago.objects.create(nombre='PayPal Filter', activo=True)

        activos = MetodoPago.objects.filter(activo=True)
        self.assertEqual(activos.count(), 2)

        tarjetas = MetodoPago.objects.filter(nombre__icontains='Tarjeta')
        self.assertEqual(tarjetas.count(), 2)

    def test_nombre_strip_espacios(self):
        """Test limpieza de espacios en nombre"""
        nombres = ['PayPal (Online)', 'Visa/Mastercard', 'Bitcoin - BTC', '  Zelle @ USA  ']
        for n in nombres:
            obj = MetodoPago.objects.create(nombre=n)
            self.assertEqual(obj.nombre, n.strip())  # Limpieza de espacios
