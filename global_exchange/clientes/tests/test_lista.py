# clientes/tests/test_modal_views.py
from django.test import TestCase, Client
from django.urls import reverse
from usuarios.models import CustomUser as User
from clientes.models import Cliente, Segmentacion

class ClienteModalViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        # Crear superusuario
        self.superadmin = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='admin123',
            cedula='TEST12345'
        )
        # Crear usuario normal
        self.user = User.objects.create_user(
            username='user',
            email='user@test.com',
            password='user123',
            cedula='TEST2312'
        )
        # Crear segmentaciones
        self.segmentacion = Segmentacion.objects.create(nombre="VIP")
        # Crear cliente de prueba
        self.cliente = Cliente.objects.create(
            nombre="Cliente Test",
            email="cliente@test.com",
            telefono="12345678",
            segmentacion=self.segmentacion,
            estado="activo"
        )

    # =======================
    # Crear Cliente (Modal)
    # =======================
    def test_create_cliente_post_superadmin(self):
        self.client.login(username='admin', password='admin123')
        url = reverse('clientes-agregar')
        data = {
            'nombre': 'Nuevo Cliente',
            'email': 'nuevo@test.com',
            'telefono': '87654321',
            'segmentacion': self.segmentacion.id,
            'estado': 'activo'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)  # Redirección
        self.assertTrue(Cliente.objects.filter(nombre='Nuevo Cliente').exists())

    def test_create_cliente_post_normal_user_redirect(self):
        self.client.login(username='user', password='user123')
        url = reverse('clientes-agregar')
        data = {
            'nombre': 'No Permitido',
            'email': 'nopermitido@test.com',
            'telefono': '11111111',
            'segmentacion': self.segmentacion.id,
            'estado': 'activo'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)  # Redirige a home
        self.assertFalse(Cliente.objects.filter(nombre='No Permitido').exists())

    # =======================
    # Editar Cliente (Modal)
    # =======================
    def test_edit_cliente_post_superadmin(self):
        self.client.login(username='admin', password='admin123')
        url = reverse('clientes-editar', args=[self.cliente.id])
        data = {
            'nombre': 'Cliente Modificado',
            'email': 'modificado@gmail.com',
            'telefono': '99999999',
            'segmentacion': self.segmentacion.id,
            'estado': 'inactivo'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        self.cliente.refresh_from_db()
        self.assertEqual(self.cliente.nombre, 'Cliente Modificado')
        self.assertEqual(self.cliente.estado, 'inactivo')

    # =======================
    # Eliminar Cliente (Modal)
    # =======================
    def test_delete_cliente_post_superadmin(self):
        self.client.login(username='admin', password='admin123')
        url = reverse('clientes-eliminar', args=[self.cliente.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Cliente.objects.filter(id=self.cliente.id).exists())

    def test_delete_cliente_post_normal_user_redirect(self):
        self.client.login(username='user', password='user123')
        url = reverse('clientes-eliminar', args=[self.cliente.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Cliente.objects.filter(id=self.cliente.id).exists())
