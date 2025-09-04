# roles_permisos/tests/test_forms.py
from django.test import TestCase
from django.contrib.admin.widgets import FilteredSelectMultiple
from usuarios.models import CustomUser
from clientes.models import Cliente
from roles_permisos.models import Usuario_Cliente
from roles_permisos.forms import ClienteUsuariosForm


class ClienteUsuariosFormTest(TestCase):
    """Tests para el formulario ClienteUsuariosForm"""
    
    def setUp(self):
        """Configuración inicial para cada test"""
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
        self.usuario3 = CustomUser.objects.create_user(
            username='usuario3',
            email='user3@test.com',
            password='testpass123',
            cedula='12345680'
        )
        
        # Crear cliente de prueba
        self.cliente = Cliente.objects.create(
            nombre='Cliente Test',
            cedula='87654321',
            email='cliente@test.com',
            telefono='123456789'
        )
        
    def test_form_fields_configuration(self):
        """Test configuración básica de campos del formulario"""
        form = ClienteUsuariosForm()
        
        # Verificar que el campo usuarios existe
        self.assertIn('usuarios', form.fields)
        
        # Verificar configuración del campo usuarios
        usuarios_field = form.fields['usuarios']
        self.assertEqual(usuarios_field.label, "Usuarios asignados")
        self.assertFalse(usuarios_field.required)
        self.assertIsInstance(usuarios_field.widget, FilteredSelectMultiple)
        
        # Verificar queryset del campo
        self.assertEqual(
            list(usuarios_field.queryset), 
            list(CustomUser.objects.all())
        )
        
    def test_form_meta_configuration(self):
        """Test configuración Meta del formulario"""
        form = ClienteUsuariosForm()
        
        self.assertEqual(form._meta.model, Cliente)
        self.assertEqual(form._meta.fields, ['usuarios'])
        
    def test_form_init_without_instance(self):
        """Test inicialización del formulario sin instancia"""
        form = ClienteUsuariosForm()
        
        # Verificar que no hay usuarios iniciales sin instancia
        self.assertIsNone(form.fields['usuarios'].initial)
        
    def test_form_init_with_existing_cliente(self):
        """Test inicialización del formulario con cliente existente"""
        # Crear relaciones Usuario_Cliente
        Usuario_Cliente.objects.create(id_usuario=self.usuario1, id_cliente=self.cliente)
        Usuario_Cliente.objects.create(id_usuario=self.usuario2, id_cliente=self.cliente)
        
        form = ClienteUsuariosForm(instance=self.cliente)
        
        # Verificar que los usuarios asignados se precargan
        usuarios_iniciales = list(form.fields['usuarios'].initial)
        self.assertEqual(len(usuarios_iniciales), 2)
        self.assertIn(self.usuario1, usuarios_iniciales)
        self.assertIn(self.usuario2, usuarios_iniciales)
        
    def test_form_valid_data_new_cliente(self):
        """Test formulario con datos válidos para nuevo cliente"""
        form_data = {
            'usuarios': [self.usuario1.id, self.usuario2.id]
        }
        form = ClienteUsuariosForm(data=form_data, instance=self.cliente)
        
        self.assertTrue(form.is_valid())
        
    def test_form_valid_without_usuarios(self):
        """Test formulario válido sin usuarios seleccionados"""
        form_data = {}
        form = ClienteUsuariosForm(data=form_data, instance=self.cliente)
        
        self.assertTrue(form.is_valid())
        
    def test_form_save_creates_usuario_cliente_relationships(self):
        """Test que el save crea las relaciones Usuario_Cliente correctamente"""
        form_data = {
            'usuarios': [self.usuario1.id, self.usuario2.id]
        }
        form = ClienteUsuariosForm(data=form_data, instance=self.cliente)
        
        self.assertTrue(form.is_valid())
        cliente = form.save()
        
        # Verificar que se crearon las relaciones
        self.assertEqual(Usuario_Cliente.objects.filter(id_cliente=cliente).count(), 2)
        self.assertTrue(
            Usuario_Cliente.objects.filter(id_usuario=self.usuario1, id_cliente=cliente).exists()
        )
        self.assertTrue(
            Usuario_Cliente.objects.filter(id_usuario=self.usuario2, id_cliente=cliente).exists()
        )
        
    def test_form_save_deletes_previous_relationships(self):
        """Test que el save elimina relaciones anteriores"""
        # Crear relaciones iniciales
        Usuario_Cliente.objects.create(id_usuario=self.usuario1, id_cliente=self.cliente)
        Usuario_Cliente.objects.create(id_usuario=self.usuario2, id_cliente=self.cliente)
        
        # Verificar que existen 2 relaciones inicialmente
        self.assertEqual(Usuario_Cliente.objects.filter(id_cliente=self.cliente).count(), 2)
        
        # Actualizar con solo un usuario
        form_data = {
            'usuarios': [self.usuario3.id]
        }
        form = ClienteUsuariosForm(data=form_data, instance=self.cliente)
        
        self.assertTrue(form.is_valid())
        cliente = form.save()
        
        # Verificar que ahora solo hay 1 relación
        self.assertEqual(Usuario_Cliente.objects.filter(id_cliente=cliente).count(), 1)
        self.assertTrue(
            Usuario_Cliente.objects.filter(id_usuario=self.usuario3, id_cliente=cliente).exists()
        )
        self.assertFalse(
            Usuario_Cliente.objects.filter(id_usuario=self.usuario1, id_cliente=cliente).exists()
        )
        self.assertFalse(
            Usuario_Cliente.objects.filter(id_usuario=self.usuario2, id_cliente=cliente).exists()
        )
        
    def test_form_save_empty_usuarios_deletes_all_relationships(self):
        """Test que guardar sin usuarios elimina todas las relaciones"""
        # Crear relaciones iniciales
        Usuario_Cliente.objects.create(id_usuario=self.usuario1, id_cliente=self.cliente)
        Usuario_Cliente.objects.create(id_usuario=self.usuario2, id_cliente=self.cliente)
        
        # Verificar que existen relaciones inicialmente
        self.assertEqual(Usuario_Cliente.objects.filter(id_cliente=self.cliente).count(), 2)
        
        # Guardar sin usuarios
        form_data = {}
        form = ClienteUsuariosForm(data=form_data, instance=self.cliente)
        
        self.assertTrue(form.is_valid())
        cliente = form.save()
        
        # Verificar que no hay relaciones
        self.assertEqual(Usuario_Cliente.objects.filter(id_cliente=cliente).count(), 0)
        
    def test_form_save_with_commit_false(self):
        """Test save con commit=False"""
        form_data = {
            'usuarios': [self.usuario1.id]
        }
        form = ClienteUsuariosForm(data=form_data, instance=self.cliente)
        
        self.assertTrue(form.is_valid())
        cliente = form.save(commit=False)
        
        # Verificar que el cliente se retorna pero las relaciones no se crean aún
        self.assertEqual(cliente, self.cliente)
        self.assertEqual(Usuario_Cliente.objects.filter(id_cliente=cliente).count(), 0)
        
        # Guardar manualmente y verificar que las relaciones se crean
        cliente.save()
        # Note: Las relaciones Usuario_Cliente no se crean automáticamente con commit=False
        # pero el código del form no maneja este caso completamente
        
    def test_form_bulk_create_efficiency(self):
        """Test que el formulario usa bulk_create para eficiencia"""
        usuarios_ids = [self.usuario1.id, self.usuario2.id, self.usuario3.id]
        form_data = {
            'usuarios': usuarios_ids
        }
        form = ClienteUsuariosForm(data=form_data, instance=self.cliente)
        
        self.assertTrue(form.is_valid())
        
        # Contar queries antes del save
        with self.assertNumQueries(3):  # DELETE + SELECT + BULK_CREATE
            cliente = form.save()
        
        # Verificar que se crearon todas las relaciones
        self.assertEqual(Usuario_Cliente.objects.filter(id_cliente=cliente).count(), 3)
        
    def test_form_widget_configuration(self):
        """Test configuración del widget FilteredSelectMultiple"""
        form = ClienteUsuariosForm()
        widget = form.fields['usuarios'].widget
        
        self.assertIsInstance(widget, FilteredSelectMultiple)
        self.assertEqual(widget.verbose_name, "Usuarios asignados")
        self.assertFalse(widget.is_stacked)
        
    def test_form_preserves_cliente_data(self):
        """Test que el formulario preserva los datos del cliente"""
        original_nombre = self.cliente.nombre
        original_cedula = self.cliente.cedula
        
        form_data = {
            'usuarios': [self.usuario1.id]
        }
        form = ClienteUsuariosForm(data=form_data, instance=self.cliente)
        
        self.assertTrue(form.is_valid())
        cliente = form.save()
        
        # Verificar que los datos del cliente no cambiaron
        self.assertEqual(cliente.nombre, original_nombre)
        self.assertEqual(cliente.cedula, original_cedula)
        
    def test_form_handles_nonexistent_usuario_ids(self):
        """Test manejo de IDs de usuarios que no existen"""
        form_data = {
            'usuarios': [9999, 9998]  # IDs que no existen
        }
        form = ClienteUsuariosForm(data=form_data, instance=self.cliente)
        
        # El formulario debería ser inválido
        self.assertFalse(form.is_valid())
        self.assertIn('usuarios', form.errors)