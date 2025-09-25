# roles_permisos/tests/test_views.py

from django.test import TestCase, Client
from django.urls import reverse
from django.http import JsonResponse
from django.contrib.auth.models import Group
import json
import uuid
from usuarios.models import CustomUser
from clientes.models import Cliente, Segmentacion
from cliente_usuario.models import Usuario_Cliente
from cliente_usuario.forms import ClienteUsuariosForm


class ClienteUsuariosViewsTest(TestCase):
    """Tests para las vistas de cliente-usuarios"""

    def setUp(self):
        self.client = Client()

        # Crear segmentación
        self.segmentacion = Segmentacion.objects.create(nombre="Segmentación Prueba")

        # Crear usuarios de prueba
        self.usuario1 = CustomUser.objects.create_user(
            username='usuario1',
            email='user1@test.com',
            password='testpass123',
            cedula='123456789'
        )
        self.usuario2 = CustomUser.objects.create_user(
            username='usuario2',
            email='user2@test.com',
            password='testpass123',
            cedula='123456780'
        )

        # Crear clientes de prueba
        self.cliente1 = Cliente.objects.create(
            nombre='Cliente Test 1',
            cedula='9876543210',
            email='cliente1@test.com',
            telefono='123456789',
            segmentacion=self.segmentacion
        )
        self.cliente2 = Cliente.objects.create(
            nombre='Cliente Test 2',
            cedula='987654321',
            email='cliente2@test.com',
            telefono='123456790',
            segmentacion=self.segmentacion
        )

        # Crear relación inicial
        Usuario_Cliente.objects.create(id_usuario=self.usuario1, id_cliente=self.cliente1)

        # Crear usuario admin global
        self.grupo_admin, _ = Group.objects.get_or_create(name='ADMIN')
        self.user_admin = CustomUser.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='adminpass',
            is_staff=True,
            is_superuser=True
        )
        self.user_admin.groups.add(self.grupo_admin)
        self.user_admin.save()
        self.client.login(username='admin', password='adminpass')


    def test_cliente_usuarios_lista_view(self):
        """Test vista lista de cliente-usuarios"""
        response = self.client.get(reverse('cliente_usuario'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Cliente Test 1')
        self.assertContains(response, 'Cliente Test 2')
        self.assertContains(response, 'usuario1')
        self.assertContains(response, 'usuario2')

        # Verificar contexto
        self.assertIn('usuarios', response.context)
        self.assertIn('clientes', response.context)
        self.assertIn('form', response.context)

        usuarios_context = list(response.context['usuarios'])
        clientes_context = list(response.context['clientes'])

        self.assertIn(self.usuario1, usuarios_context)
        self.assertIn(self.usuario2, usuarios_context)
        self.assertIn(self.cliente1, clientes_context)
        self.assertIn(self.cliente2, clientes_context)
        self.assertIsInstance(response.context['form'], ClienteUsuariosForm)

    def test_cliente_usuarios_lista_template_used(self):
        response = self.client.get(reverse('cliente_usuario'))
        self.assertTemplateUsed(response, 'lista.html')

    def test_cliente_usuarios_lista_ordering(self):
        response = self.client.get(reverse('cliente_usuario'))
        clientes_context = list(response.context['clientes'])
        self.assertEqual(clientes_context[0], self.cliente2)
        self.assertEqual(clientes_context[1], self.cliente1)

    def test_editar_cliente_usuario_get(self):
        """Test GET para editar asignación cliente-usuario"""
        response = self.client.get(reverse('editar_cliente_usuario', kwargs={'id': self.cliente1.id}))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'lista.html')

        context = response.context
        self.assertIn('form', context)
        self.assertIn('usuarios', context)
        self.assertIn('usuarios_asignados', context)
        self.assertTrue(context['show_modal'])
        self.assertEqual(context['modal_type'], 'edit')
        self.assertEqual(context['obj_id'], self.cliente1.id)
        self.assertIn(self.usuario1.id, context['usuarios_asignados'])

    def test_editar_cliente_usuario_post_valid(self):
        """Test POST válido para editar asignación"""
        post_data = {'usuarios': [self.usuario2.id]}

        response = self.client.post(reverse('editar_cliente_usuario', kwargs={'id': self.cliente1.id}),
                                    data=post_data)

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('cliente_usuario'))

        self.assertTrue(Usuario_Cliente.objects.filter(id_usuario=self.usuario2, id_cliente=self.cliente1).exists())

    def test_editar_cliente_usuario_post_invalid(self):
        """Test POST inválido para editar asignación"""
        post_data = {'usuarios': [9999]}  # Usuario inexistente

        response = self.client.post(reverse('editar_cliente_usuario', kwargs={'id': self.cliente1.id}),
                                    data=post_data)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'lista.html')
        form = response.context['form']
        self.assertFalse(form.is_valid())

    def test_editar_cliente_usuario_nonexistent_cliente(self):
        """Test editar con cliente que no existe"""
        response = self.client.get(reverse('editar_cliente_usuario', kwargs={'id': 9999}))
        self.assertEqual(response.status_code, 404)

    def test_cliente_usuario_detalle_ajax_view(self):
        response = self.client.get(reverse('cliente_usuario_detalle', kwargs={'pk': self.cliente1.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response, JsonResponse)
        data = json.loads(response.content)
        self.assertIn('usuarios', data)
        self.assertIn('modal_title', data)
        self.assertEqual(data['modal_title'], 'Editar Asignación')
        usuarios_ids = data['usuarios']
        self.assertIn(str(self.usuario1.id), usuarios_ids)

    def test_cliente_usuario_detalle_ajax_nonexistent_cliente(self):
        response = self.client.get(reverse('cliente_usuario_detalle', kwargs={'pk': 9999}))
        self.assertEqual(response.status_code, 404)

    def test_cliente_usuario_detalle_multiple_usuarios(self):
        Usuario_Cliente.objects.create(id_usuario=self.usuario2, id_cliente=self.cliente1)
        response = self.client.get(reverse('cliente_usuario_detalle', kwargs={'pk': self.cliente1.pk}))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        usuarios_ids = data['usuarios']
        self.assertEqual(len(usuarios_ids), 2)
        self.assertIn(str(self.usuario1.id), usuarios_ids)
        self.assertIn(str(self.usuario2.id), usuarios_ids)

    def test_cliente_usuario_detalle_no_usuarios_asignados(self):
        response = self.client.get(reverse('cliente_usuario_detalle', kwargs={'pk': self.cliente2.pk}))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        usuarios_ids = data['usuarios']
        self.assertEqual(len(usuarios_ids), 0)

    def test_view_context_data_completeness(self):
        response = self.client.get(reverse('cliente_usuario'))
        for key in ['usuarios', 'clientes', 'form']:
            self.assertIn(key, response.context)

        response = self.client.get(reverse('editar_cliente_usuario', kwargs={'id': self.cliente1.id}))
        for key in ['form', 'usuarios', 'usuarios_asignados', 'show_modal', 'modal_type', 'obj_id']:
            self.assertIn(key, response.context)

    def test_form_instance_in_edit_view(self):
        response = self.client.get(reverse('editar_cliente_usuario', kwargs={'id': self.cliente1.id}))
        form = response.context['form']
        self.assertEqual(form.instance, self.cliente1)
