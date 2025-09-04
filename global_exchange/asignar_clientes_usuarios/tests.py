from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from clientes.models import Cliente, Segmentacion
from roles_permisos.models import Rol
from .models import Usuario_Rol_Cliente

User = get_user_model()


class UsuarioRolClienteModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="admin", password="12345", is_superuser=True)
        self.seg = Segmentacion.objects.create(nombre="VIP", descuento=10.0)
        self.cliente = Cliente.objects.create(nombre="Juan", email="juan@example.com", segmentacion=self.seg)

    def test_str_representation(self):
        asignacion = Usuario_Rol_Cliente.objects.create(id_usuario=self.user, id_cliente=self.cliente)
        self.assertEqual(str(asignacion), f"{self.user.username} - {self.cliente.nombre}")


class UsuarioRolClienteViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="admin", password="12345", is_superuser=True)
        self.client.login(username="admin", password="12345")
        self.seg = Segmentacion.objects.create(nombre="VIP", descuento=10.0)
        self.cliente = Cliente.objects.create(nombre="Juan", email="juan@example.com", segmentacion=self.seg)
        self.rol = Rol.objects.create(nombre="SuperAdmin")
        self.asignacion = Usuario_Rol_Cliente.objects.create(id_usuario=self.user, id_cliente=self.cliente)

    def test_lista_usuarios_roles_view(self):
        response = self.client.get(reverse("usuarios_roles_lista"))
        self.assertEqual(response.status_code, 200)

    def test_crear_usuario_rol_view(self):
        new_user = User.objects.create_user(username="user2", password="12345")
        response = self.client.post(reverse("usuarios_roles_crear"), {
            "usuario": new_user.id,
            "cliente": self.cliente.id,
            "rol": self.rol.id
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Usuario_Rol_Cliente.objects.filter(id_usuario=new_user, id_cliente=self.cliente).exists())
        new_user.refresh_from_db()
        self.assertEqual(new_user.rol, self.rol)

    def test_editar_usuario_rol_view(self):
        new_user = User.objects.create_user(username="user3", password="12345")
        response = self.client.post(reverse("usuarios_roles_editar", args=[self.asignacion.id]), {
            "usuario": new_user.id,
            "cliente": self.cliente.id,
            "rol": self.rol.id
        })
        self.assertEqual(response.status_code, 302)
        self.asignacion.refresh_from_db()
        self.assertEqual(self.asignacion.id_usuario, new_user)
        new_user.refresh_from_db()
        self.assertEqual(new_user.rol, self.rol)

    def test_eliminar_usuario_rol_view(self):
        response = self.client.post(reverse("usuarios_roles_eliminar", args=[self.asignacion.id]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Usuario_Rol_Cliente.objects.filter(id=self.asignacion.id).exists())
