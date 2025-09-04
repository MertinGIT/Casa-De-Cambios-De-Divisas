from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from clientes.models import Cliente, Segmentacion
from django.contrib.auth import get_user_model

User = get_user_model()

class ClienteViewsTest(TestCase):
    def setUp(self):
        # Usuario superadmin
        self.superadmin = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='password123',
            cedula='0001'
        )
        # Usuario normal
        self.user = User.objects.create_user(
            username='user',
            email='user@example.com',
            password='password123',
            cedula='0002'
        )

        # Segmentación de prueba
        self.segmentacion = Segmentacion.objects.create(
            nombre="Regular",
            descripcion="Cliente regular",
            descuento=10
        )

        # Cliente de prueba
        self.cliente = Cliente.objects.create(
            nombre="Juan",
            email="juan@example.com",
            telefono="12345678",
            segmentacion=self.segmentacion,
            estado="activo"
        )

    # ======================= Acceso =======================
    def test_clientes_view_superadmin(self):
        self.client.login(username='admin', password='password123')
        url = reverse('clientes')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'clientes/lista.html')

    def test_clientes_view_normal_user_redirect(self):
        self.client.login(username='user', password='password123')
        url = reverse('clientes')
        response = self.client.get(url)
        self.assertRedirects(response, reverse('home'))

    def test_clientes_view_not_logged_redirect(self):
        url = reverse('clientes')
        response = self.client.get(url)
        self.assertRedirects(response, reverse('login'))

    # ======================= ListView =======================
    def test_cliente_list_view_superadmin(self):
        self.client.login(username='admin', password='password123')
        url = reverse('clientes')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.cliente, response.context['clientes'])
        self.assertIn(self.segmentacion, response.context['segmentaciones'])

    # ======================= CreateView =======================
    def test_cliente_create_view_post(self):
        self.client.login(username='admin', password='password123')
        url = reverse('clientes-agregar')
        data = {
            'nombre': 'Pedro',
            'email': 'pedro@example.com',
            'telefono': '5555',
            'segmentacion': self.segmentacion.id,
            'estado': 'activo'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Cliente.objects.filter(email='pedro@example.com').exists())

    # ======================= UpdateView =======================
    def test_cliente_update_view_post(self):
        self.client.login(username='admin', password='password123')
        url = reverse('clientes-editar', args=[self.cliente.id])
        data = {
            'nombre': 'Juan Modificado',
            'email': 'juan@example.com',
            'telefono': '9999',
            'segmentacion': self.segmentacion.id,
            'estado': 'activo'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        self.cliente.refresh_from_db()
        self.assertEqual(self.cliente.nombre, 'Juan Modificado')
        self.assertEqual(self.cliente.telefono, '9999')

    # ======================= DeleteView =======================
    def test_cliente_delete_view_post(self):
        self.client.login(username='admin', password='password123')
        url = reverse('clientes-eliminar', args=[self.cliente.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Cliente.objects.filter(id=self.cliente.id).exists())
