# cliente_usuario/tests/test_forms.py

from django.test import TestCase
from django.contrib.admin.widgets import FilteredSelectMultiple
from clientes.models import Cliente, Segmentacion  # Ajusta según tu modelo real
from usuarios.models import CustomUser
from cliente_usuario.models import Usuario_Cliente
from cliente_usuario.forms import ClienteUsuariosForm


class ClienteUsuariosFormTest(TestCase):
    """Tests para el formulario ClienteUsuariosForm"""
    
    def setUp(self):
        """Configuración inicial para cada test"""
        # Crear segmentación obligatoria para clientes
        self.segmentacion = Segmentacion.objects.create(
            nombre="Segmentación Test"
        )

        # Crear cliente
        self.cliente = Cliente.objects.create(
            nombre="Cliente Test",
            segmentacion=self.segmentacion
        )

        # Crear usuarios
        self.usuario1 = CustomUser.objects.create_user(
            username="user1", password="testpass"
        )
        self.usuario2 = CustomUser.objects.create_user(
            username="user2", password="testpass"
        )

    def test_init_precarga_usuarios(self):
        """El formulario debe precargar usuarios asignados a un cliente existente"""
        # Crear relación inicial usuario-cliente
        Usuario_Cliente.objects.create(id_usuario=self.usuario1, id_cliente=self.cliente)

        form = ClienteUsuariosForm(instance=self.cliente)
        self.assertIn(self.usuario1, form.fields['usuarios'].initial)

    def test_save_asigna_usuarios(self):
        """Guardar el formulario debe asignar usuarios correctamente"""
        data = {'usuarios': [self.usuario1.id, self.usuario2.id]}
        form = ClienteUsuariosForm(data=data, instance=self.cliente)
        self.assertTrue(form.is_valid(), form.errors)

        form.save()

        asignados = Usuario_Cliente.objects.filter(id_cliente=self.cliente)
        self.assertEqual(asignados.count(), 2)
        self.assertTrue(asignados.filter(id_usuario=self.usuario1).exists())
        self.assertTrue(asignados.filter(id_usuario=self.usuario2).exists())

    def test_save_elimina_relaciones_previas(self):
        """Guardar el formulario debe eliminar relaciones anteriores y crear nuevas"""
        # Crear relación inicial
        Usuario_Cliente.objects.create(id_usuario=self.usuario1, id_cliente=self.cliente)

        # Guardar solo con usuario2
        data = {'usuarios': [self.usuario2.id]}
        form = ClienteUsuariosForm(data=data, instance=self.cliente)
        self.assertTrue(form.is_valid(), form.errors)
        form.save()

        asignados = Usuario_Cliente.objects.filter(id_cliente=self.cliente)
        self.assertEqual(asignados.count(), 1)
        self.assertTrue(asignados.filter(id_usuario=self.usuario2).exists())
        self.assertFalse(asignados.filter(id_usuario=self.usuario1).exists())

    def test_save_sin_usuarios(self):
        """Si no se asignan usuarios, no debe haber relaciones en la tabla intermedia"""
        data = {'usuarios': []}
        form = ClienteUsuariosForm(data=data, instance=self.cliente)
        self.assertTrue(form.is_valid(), form.errors)
        form.save()

        asignados = Usuario_Cliente.objects.filter(id_cliente=self.cliente)
        self.assertEqual(asignados.count(), 0)
