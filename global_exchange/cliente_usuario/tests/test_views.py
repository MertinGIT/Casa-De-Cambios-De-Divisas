# roles_permisos/tests/test_views.py
from django.test import TestCase, Client
from django.urls import reverse
from django.http import JsonResponse
from django.contrib.auth.models import User
import json

from usuarios.models import CustomUser
from clientes.models import Cliente
from cliente_usuario.models import Usuario_Cliente
from cliente_usuario.forms import ClienteUsuariosForm


class ClienteUsuariosViewsTest(TestCase):
    """Tests para las vistas de cliente-usuarios"""
    
    def setUp(self):
        """Configuración inicial para cada test"""
        self.client = Client()
        
        # Crear usuarios de prueba
        self.usuario1 = CustomUser.objects.create_user(
            username='usuario1',
            email='user1@test.com',
            password='testpass123',
            cedula='12345678'
        )
        self.usuario2 = CustomUser.objects.create_user(
            username='usuario2',
            email='user2@test.com',
            password='testpass123',
            cedula='12345679'
        )
        
        # Crear clientes de prueba
        self.cliente1 = Cliente.objects.create(
            nombre='Cliente Test 1',
            cedula='87654321',
            email='cliente1@test.com',
            telefono='123456789'
        )
        self.cliente2 = Cliente.objects.create(
            nombre='Cliente Test 2',
            cedula='87654322',
            email='cliente2@test.com',
            telefono='123456790'
        )
        
        # Crear algunas relaciones Usuario_Cliente
        Usuario_Cliente.objects.create(id_usuario=self.usuario1, id_cliente=self.cliente1)
        
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
        
        # Verificar que se envían los datos correctos
        usuarios_context = list(response.context['usuarios'])
        clientes_context = list(response.context['clientes'])
        
        self.assertIn(self.usuario1, usuarios_context)
        self.assertIn(self.usuario2, usuarios_context)
        self.assertIn(self.cliente1, clientes_context)
        self.assertIn(self.cliente2, clientes_context)
        
        # Verificar que el formulario es una instancia de ClienteUsuariosForm
        self.assertIsInstance(response.context['form'], ClienteUsuariosForm)
        
    def test_cliente_usuarios_lista_template_used(self):
        """Test que se usa la plantilla correcta"""
        response = self.client.get(reverse('cliente_usuario'))
        
        self.assertTemplateUsed(response, 'lista.html')
        
    def test_cliente_usuarios_lista_ordering(self):
        """Test que los clientes se ordenan por ID descendente"""
        response = self.client.get(reverse('cliente_usuario'))
        
        clientes_context = list(response.context['clientes'])
        
        # Verificar que cliente2 (ID mayor) aparece antes que cliente1
        self.assertEqual(clientes_context[0], self.cliente2)
        self.assertEqual(clientes_context[1], self.cliente1)
        
    def test_editar_cliente_usuario_get(self):
        """Test GET para editar asignación cliente-usuario"""
        response = self.client.get(
            reverse('editar_cliente_usuario', kwargs={'id': self.cliente1.id})
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'lista.html')
        
        # Verificar contexto específico para modal de edición
        context = response.context
        self.assertIn('form', context)
        self.assertIn('usuarios', context)
        self.assertIn('usuarios_asignados', context)
        self.assertTrue(context['show_modal'])
        self.assertEqual(context['modal_type'], 'edit')
        self.assertEqual(context['obj_id'], self.cliente1.id)
        
        # Verificar usuarios asignados
        usuarios_asignados = context['usuarios_asignados']
        self.assertIn(self.usuario1.id, usuarios_asignados)
        
    def test_editar_cliente_usuario_post_valid(self):
        """Test POST válido para editar asignación"""
        post_data = {
            'usuarios': [self.usuario2.id]  # Cambiar de usuario1 a usuario2
        }
        
        response = self.client.post(
            reverse('editar_cliente_usuario', kwargs={'id': self.cliente1.id}),
            data=post_data
        )
        
        # Verificar redirección después de éxito
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('cliente_usuario'))
        
        # Verificar que se actualizó la asignación
        self.assertFalse(
            Usuario_Cliente.objects.filter(
                id_usuario=self.usuario1, 
                id_cliente=self.cliente1
            ).exists()
        )
        self.assertTrue(
            Usuario_Cliente.objects.filter(
                id_usuario=self.usuario2, 
                id_cliente=self.cliente1
            ).exists()
        )
        
    def test_editar_cliente_usuario_post_invalid(self):
        """Test POST inválido para editar asignación"""
        # Datos inválidos (usuario que no existe)
        post_data = {
            'usuarios': [9999]
        }
        
        response = self.client.post(
            reverse('editar_cliente_usuario', kwargs={'id': self.cliente1.id}),
            data=post_data
        )
        
        # Debería renderizar el template con errores en lugar de redirigir
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'lista.html')
        
        # Verificar que el formulario tiene errores
        form = response.context['form']
        self.assertFalse(form.is_valid())
        
    def test_editar_cliente_usuario_nonexistent_cliente(self):
        """Test editar con cliente que no existe"""
        response = self.client.get(
            reverse('editar_cliente_usuario', kwargs={'id': 9999})
        )
        
        self.assertEqual(response.status_code, 404)
        
    def test_cliente_usuario_detalle_ajax_view(self):
        """Test vista AJAX para obtener detalles del cliente"""
        response = self.client.get(
            reverse('cliente_usuario_detalle', kwargs={'pk': self.cliente1.pk})
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response, JsonResponse)
        
        # Verificar contenido JSON
        data = json.loads(response.content)
        self.assertIn('usuarios', data)
        self.assertIn('modal_title', data)
        self.assertEqual(data['modal_title'], 'Editar Asignación')
        
        # Verificar usuarios asignados en la respuesta
        usuarios_ids = data['usuarios']
        self.assertIn(str(self.usuario1.id), usuarios_ids)
        
    def test_cliente_usuario_detalle_ajax_nonexistent_cliente(self):
        """Test vista AJAX con cliente que no existe"""
        response = self.client.get(
            reverse('cliente_usuario_detalle', kwargs={'pk': 9999})
        )
        
        self.assertEqual(response.status_code, 404)
        
    def test_cliente_usuario_detalle_multiple_usuarios(self):
        """Test vista AJAX con múltiples usuarios asignados"""
        # Agregar segundo usuario al cliente1
        Usuario_Cliente.objects.create(id_usuario=self.usuario2, id_cliente=self.cliente1)
        
        response = self.client.get(
            reverse('cliente_usuario_detalle', kwargs={'pk': self.cliente1.pk})
        )
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        usuarios_ids = data['usuarios']
        
        # Verificar que ambos usuarios están en la respuesta
        self.assertEqual(len(usuarios_ids), 2)
        self.assertIn(str(self.usuario1.id), usuarios_ids)
        self.assertIn(str(self.usuario2.id), usuarios_ids)
        
    def test_cliente_usuario_detalle_no_usuarios_asignados(self):
        """Test vista AJAX con cliente sin usuarios asignados"""
        response = self.client.get(
            reverse('cliente_usuario_detalle', kwargs={'pk': self.cliente2.pk})
        )
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        usuarios_ids = data['usuarios']
        
        # Verificar que no hay usuarios asignados
        self.assertEqual(len(usuarios_ids), 0)
        
    def test_view_context_data_completeness(self):
        """Test que las vistas envían todos los datos necesarios"""
        # Test vista lista
        response = self.client.get(reverse('cliente_usuario'))
        
        required_context_keys = ['usuarios', 'clientes', 'form']
        for key in required_context_keys:
            self.assertIn(key, response.context, f"Falta {key} en el contexto")
            
        # Test vista editar
        response = self.client.get(
            reverse('editar_cliente_usuario', kwargs={'id': self.cliente1.id})
        )
        
        edit_context_keys = [
            'form', 'usuarios', 'usuarios_asignados', 
            'show_modal', 'modal_type', 'obj_id'
        ]
        for key in edit_context_keys:
            self.assertIn(key, response.context, f"Falta {key} en el contexto de edición")
            
    def test_form_instance_in_edit_view(self):
        """Test que la vista de edición usa la instancia correcta del formulario"""
        response = self.client.get(
            reverse('editar_cliente_usuario', kwargs={'id': self.cliente1.id})
        )
        
        form = response.context['form']
        self.assertEqual(form.instance, self.cliente1)
        