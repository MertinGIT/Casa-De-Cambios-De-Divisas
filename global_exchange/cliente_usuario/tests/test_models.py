# tests/test_models.py

from django.test import TestCase
from usuarios.models import CustomUser
from clientes.models import Cliente, Segmentacion  # asegúrate de importar el modelo correcto
from cliente_usuario.models import Usuario_Cliente


class UsuarioClienteModelTest(TestCase):
    """Tests para el modelo Usuario_Cliente"""

    def setUp(self):
        """Configuración inicial para cada test"""
        # Crear usuario de prueba
        self.usuario = CustomUser.objects.create_user(
            username="testuser",
            password="testpassword"
        )

        # Crear segmentación de prueba (obligatoria)
        self.segmentacion = Segmentacion.objects.create(
            nombre="Segmentación Prueba"
        )

        # Crear cliente de prueba con segmentación obligatoria
        self.cliente = Cliente.objects.create(
            nombre="Cliente Prueba",
            segmentacion=self.segmentacion
        )

        # Crear relación usuario-cliente
        self.usuario_cliente = Usuario_Cliente.objects.create(
            id_usuario=self.usuario,
            id_cliente=self.cliente
        )

    def test_creacion_usuario_cliente(self):
        """Verifica que la relación Usuario_Cliente se crea correctamente"""
        self.assertEqual(self.usuario_cliente.id_usuario, self.usuario)
        self.assertEqual(self.usuario_cliente.id_cliente, self.cliente)

    def test_str_representation(self):
        """Verifica que el método __str__ devuelve 'usuario - cliente'"""
        expected_str = f"{self.usuario.username} - {self.cliente.nombre}"
        self.assertEqual(str(self.usuario_cliente), expected_str)

    def test_guardado_en_base_datos(self):
        """Verifica que el objeto se guarda en la base de datos"""
        self.assertEqual(Usuario_Cliente.objects.count(), 1)
        self.assertTrue(
            Usuario_Cliente.objects.filter(
                id_usuario=self.usuario,
                id_cliente=self.cliente
            ).exists()
        )
