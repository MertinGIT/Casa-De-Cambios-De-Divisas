from django.test import TestCase
from django.db import IntegrityError
from usuarios.models import CustomUser
from clientes.models import Cliente
from roles_permisos.models import Usuario_Cliente


class UsuarioClienteModelTest(TestCase):
    """Tests para el modelo Usuario_Cliente"""
    
    def setUp(self):
        """Configuración inicial para cada test"""
        # Crear usuario de prueba
        self.usuario = CustomUser.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            cedula='12345678'
        )
        
        # Crear cliente de prueba
        self.cliente = Cliente.objects.create(
            nombre='Cliente Test',
            cedula='87654321',
            email='cliente@test.com',
            telefono='123456789'
        )
        
    def test_usuario_cliente_creation(self):
        """Test creación básica de Usuario_Cliente"""
        usuario_cliente = Usuario_Cliente.objects.create(
            id_usuario=self.usuario,
            id_cliente=self.cliente
        )
        
        self.assertEqual(usuario_cliente.id_usuario, self.usuario)
        self.assertEqual(usuario_cliente.id_cliente, self.cliente)
        self.assertTrue(isinstance(usuario_cliente, Usuario_Cliente))
        
    def test_usuario_cliente_str_method(self):
        """Test método __str__ de Usuario_Cliente"""
        usuario_cliente = Usuario_Cliente.objects.create(
            id_usuario=self.usuario,
            id_cliente=self.cliente
        )
        
        expected_str = f"{self.usuario.username} - {self.cliente.nombre}"
        self.assertEqual(str(usuario_cliente), expected_str)
        self.assertEqual(str(usuario_cliente), "testuser - Cliente Test")
        
    def test_usuario_cliente_db_table(self):
        """Test que la tabla tenga el nombre correcto"""
        self.assertEqual(Usuario_Cliente._meta.db_table, "usuario_cliente")
        
    def test_usuario_cliente_verbose_names(self):
        """Test nombres verbose del modelo"""
        self.assertEqual(Usuario_Cliente._meta.verbose_name, "Usuario Cliente")
        self.assertEqual(Usuario_Cliente._meta.verbose_name_plural, "Usuarios Clientes")
        
    def test_usuario_foreign_key_relationship(self):
        """Test relación ForeignKey con Usuario"""
        usuario_cliente = Usuario_Cliente.objects.create(
            id_usuario=self.usuario,
            id_cliente=self.cliente
        )
        
        # Verificar relación desde Usuario_Cliente hacia Usuario
        self.assertEqual(usuario_cliente.id_usuario, self.usuario)
        
        # Verificar relación reverse desde Usuario
        self.assertTrue(self.usuario.usuario_clientes.filter(id=usuario_cliente.id).exists())
        
    def test_cliente_foreign_key_relationship(self):
        """Test relación ForeignKey con Cliente"""
        usuario_cliente = Usuario_Cliente.objects.create(
            id_usuario=self.usuario,
            id_cliente=self.cliente
        )
        
        # Verificar relación desde Usuario_Cliente hacia Cliente
        self.assertEqual(usuario_cliente.id_cliente, self.cliente)
        
        # Verificar relación reverse desde Cliente
        self.assertTrue(self.cliente.cliente_usuarios.filter(id=usuario_cliente.id).exists())
        
    def test_usuario_cascade_delete(self):
        """Test que Usuario_Cliente se elimine cuando se elimina el usuario"""
        usuario_cliente = Usuario_Cliente.objects.create(
            id_usuario=self.usuario,
            id_cliente=self.cliente
        )
        usuario_cliente_id = usuario_cliente.id
        
        # Eliminar el usuario
        self.usuario.delete()
        
        # Verificar que Usuario_Cliente también se eliminó
        with self.assertRaises(Usuario_Cliente.DoesNotExist):
            Usuario_Cliente.objects.get(id=usuario_cliente_id)
            
    def test_cliente_cascade_delete(self):
        """Test que Usuario_Cliente se elimine cuando se elimina el cliente"""
        usuario_cliente = Usuario_Cliente.objects.create(
            id_usuario=self.usuario,
            id_cliente=self.cliente
        )
        usuario_cliente_id = usuario_cliente.id
        
        # Eliminar el cliente
        self.cliente.delete()
        
        # Verificar que Usuario_Cliente también se eliminó
        with self.assertRaises(Usuario_Cliente.DoesNotExist):
            Usuario_Cliente.objects.get(id=usuario_cliente_id)
            
    def test_multiple_usuarios_same_cliente(self):
        """Test que un cliente puede tener múltiples usuarios"""
        # Crear segundo usuario
        usuario2 = CustomUser.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='testpass123',
            cedula='12345679'
        )
        
        # Crear relaciones
        usuario_cliente1 = Usuario_Cliente.objects.create(
            id_usuario=self.usuario,
            id_cliente=self.cliente
        )
        usuario_cliente2 = Usuario_Cliente.objects.create(
            id_usuario=usuario2,
            id_cliente=self.cliente
        )
        
        # Verificar que el cliente tiene 2 usuarios asignados
        self.assertEqual(self.cliente.cliente_usuarios.count(), 2)
        self.assertTrue(self.cliente.cliente_usuarios.filter(id_usuario=self.usuario).exists())
        self.assertTrue(self.cliente.cliente_usuarios.filter(id_usuario=usuario2).exists())
        
    def test_multiple_clientes_same_usuario(self):
        """Test que un usuario puede estar asignado a múltiples clientes"""
        # Crear segundo cliente
        cliente2 = Cliente.objects.create(
            nombre='Cliente Test 2',
            cedula='87654322',
            email='cliente2@test.com',
            telefono='123456790'
        )
        
        # Crear relaciones
        usuario_cliente1 = Usuario_Cliente.objects.create(
            id_usuario=self.usuario,
            id_cliente=self.cliente
        )
        usuario_cliente2 = Usuario_Cliente.objects.create(
            id_usuario=self.usuario,
            id_cliente=cliente2
        )
        
        # Verificar que el usuario tiene 2 clientes asignados
        self.assertEqual(self.usuario.usuario_clientes.count(), 2)
        self.assertTrue(self.usuario.usuario_clientes.filter(id_cliente=self.cliente).exists())
        self.assertTrue(self.usuario.usuario_clientes.filter(id_cliente=cliente2).exists())
        
    def test_unique_constraint_allows_duplicates(self):
        """Test que permite múltiples asignaciones usuario-cliente (sin constraint único)"""
        # Crear primera relación
        usuario_cliente1 = Usuario_Cliente.objects.create(
            id_usuario=self.usuario,
            id_cliente=self.cliente
        )
        
        # Intentar crear segunda relación idéntica - debería ser permitido
        # (no hay constraint único en el modelo actual)
        usuario_cliente2 = Usuario_Cliente.objects.create(
            id_usuario=self.usuario,
            id_cliente=self.cliente
        )
        
        # Verificar que ambas relaciones existen
        self.assertEqual(Usuario_Cliente.objects.filter(
            id_usuario=self.usuario,
            id_cliente=self.cliente
        ).count(), 2)
        
    def test_related_name_usuario_clientes(self):
        """Test que el related_name 'usuario_clientes' funciona correctamente"""
        usuario_cliente = Usuario_Cliente.objects.create(
            id_usuario=self.usuario,
            id_cliente=self.cliente
        )
        
        # Verificar acceso desde el usuario
        relacionados = self.usuario.usuario_clientes.all()
        self.assertEqual(len(relacionados), 1)
        self.assertEqual(relacionados[0], usuario_cliente)
        
    def test_related_name_cliente_usuarios(self):
        """Test que el related_name 'cliente_usuarios' funciona correctamente"""
        usuario_cliente = Usuario_Cliente.objects.create(
            id_usuario=self.usuario,
            id_cliente=self.cliente
        )
        
        # Verificar acceso desde el cliente
        relacionados = self.cliente.cliente_usuarios.all()
        self.assertEqual(len(relacionados), 1)
        self.assertEqual(relacionados[0], usuario_cliente)