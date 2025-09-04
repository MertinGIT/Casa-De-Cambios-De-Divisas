"""
Tests básicos para vistas de métodos de pago
"""
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from metodos_pagos.models import MetodoPago


class MetodoPagoViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        User = get_user_model()

        # Crear superusuario
        self.superuser = User.objects.create_superuser(
            username="admin",
            email="admin@test.com",
            password="admin123",
            cedula="12345678"
        )

        # Crear un método de pago inicial
        self.metodo = MetodoPago.objects.create(
            nombre="PayPal",
            descripcion="Pago online",
            activo=True
        )

    def test_login_required(self):
        """Acceso sin login debe redirigir"""
        response = self.client.get('/metodos-pagos/')
        self.assertEqual(response.status_code, 302)

    def test_superuser_access(self):
        """El superusuario puede acceder"""
        self.client.login(username="admin", password="admin123")
        response = self.client.get('/metodos-pagos/')
        self.assertEqual(response.status_code, 200)

    def test_create_metodo_pago(self):
        """Creación de método de pago"""
        self.client.login(username="admin", password="admin123")
        data = {'nombre': 'Transferencia', 'descripcion': 'Pago bancario'}
        response = self.client.post('/metodos-pagos/agregar/', data)
        self.assertTrue(MetodoPago.objects.filter(nombre="Transferencia").exists())

    def test_update_metodo_pago(self):
        """Edición de método de pago"""
        self.client.login(username="admin", password="admin123")
        data = {'nombre': 'PayPal Editado', 'descripcion': 'Actualizado'}
        response = self.client.post(f'/metodos-pagos/{self.metodo.pk}/editar/', data)
        self.metodo.refresh_from_db()
        self.assertEqual(self.metodo.nombre, "PayPal Editado")

    def test_activate_metodo_pago(self):
        """Activar método de pago"""
        self.client.login(username="admin", password="admin123")
        self.metodo.activo = False
        self.metodo.save()
        
        response = self.client.post(f'/metodos-pagos/{self.metodo.pk}/activar/')
        self.metodo.refresh_from_db()
        self.assertTrue(self.metodo.activo)

    def test_deactivate_metodo_pago(self):
        """Desactivar método de pago"""
        self.client.login(username="admin", password="admin123")
        response = self.client.post(f'/metodos-pagos/{self.metodo.pk}/desactivar/')
        self.metodo.refresh_from_db()
        self.assertFalse(self.metodo.activo)

    def test_detalle_json(self):
        """Vista detalle JSON"""
        response = self.client.get(f'/metodos-pagos/{self.metodo.pk}/detalle/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['nombre'], "PayPal")
        self.assertEqual(data['descripcion'], "Pago online")
        self.assertTrue(data['activo'])

    def test_validar_nombre_disponible(self):
        """Validación AJAX nombre disponible"""
        self.client.login(username="admin", password="admin123")
        response = self.client.post('/metodos-pagos/validar-nombre/', {
            'nombre': 'Nuevo Método',
            'current_id': ''
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['valid'])
        self.assertEqual(data['message'], 'Disponible')

    def test_validar_nombre_existente(self):
        """Validación AJAX nombre existente"""
        self.client.login(username="admin", password="admin123")
        response = self.client.post('/metodos-pagos/validar-nombre/', {
            'nombre': 'paypal',
            'current_id': ''
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data['valid'])
        self.assertEqual(data['message'], 'El método de pago ya existe.')