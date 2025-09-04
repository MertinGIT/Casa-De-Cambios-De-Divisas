from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Rol, Permiso

class RolesPermisosTestCase(TestCase):
    def setUp(self):
        # Cliente de prueba
        self.client = Client()

        # Crear usuario superadmin
        self.superadmin = User.objects.create_superuser(
            username="admin", email="admin@test.com", password="admin123"
        )

        # Crear usuario normal
        self.user = User.objects.create_user(
            username="normal", email="user@test.com", password="user123"
        )

        # Crear permisos
        self.permiso1 = Permiso.objects.create(nombre="Crear")
        self.permiso2 = Permiso.objects.create(nombre="Editar")

        # Crear rol inicial
        self.rol = Rol.objects.create(nombre="Administrador", descripcion="Rol admin")
        self.rol.permisos.add(self.permiso1)

    def test_lista_roles_superadmin(self):
        self.client.login(username="admin", password="admin123")
        response = self.client.get(reverse("roles"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "roles/lista.html")
        self.assertContains(response, "Administrador")

    def test_lista_roles_usuario_normal(self):
        self.client.login(username="normal", password="user123")
        response = self.client.get(reverse("roles"))
        self.assertRedirects(response, reverse("home"))

    def test_crear_rol_valido(self):
        self.client.login(username="admin", password="admin123")
        response = self.client.post(reverse("rol_nuevo"), {
            "nombre": "Supervisor",
            "descripcion": "Gestiona usuarios",
            "permisos": [self.permiso1.id, self.permiso2.id]
        })
        self.assertRedirects(response, reverse("roles"))
        self.assertTrue(Rol.objects.filter(nombre="Supervisor").exists())

    def test_crear_rol_invalido(self):
        self.client.login(username="admin", password="admin123")
        response = self.client.post(reverse("rol_nuevo"), {
            "nombre": "",  # inválido
            "descripcion": "Sin nombre",
        })
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "roles/lista.html")
        self.assertContains(response, "show_modal")

    def test_editar_rol_valido(self):
        self.client.login(username="admin", password="admin123")
        response = self.client.post(reverse("rol_editar", args=[self.rol.id]), {
            "nombre": "Administrador Editado",
            "descripcion": "Descripción editada",
            "permisos": [self.permiso2.id]
        })
        self.assertRedirects(response, reverse("roles"))
        self.rol.refresh_from_db()
        self.assertEqual(self.rol.nombre, "Administrador Editado")
        self.assertIn(self.permiso2, self.rol.permisos.all())

    def test_editar_rol_invalido(self):
        self.client.login(username="admin", password="admin123")
        response = self.client.post(reverse("rol_editar", args=[self.rol.id]), {
            "nombre": "",  # inválido
            "descripcion": "Error"
        })
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "roles/form.html")

    def test_eliminar_rol_post(self):
        self.client.login(username="admin", password="admin123")
        response = self.client.post(reverse("rol_eliminar", args=[self.rol.id]))
        self.assertRedirects(response, reverse("roles"))
        self.assertFalse(Rol.objects.filter(id=self.rol.id).exists())

    def test_eliminar_rol_get(self):
        self.client.login(username="admin", password="admin123")
        response = self.client.get(reverse("rol_eliminar", args=[self.rol.id]))
        self.assertRedirects(response, reverse("roles"))
        self.assertTrue(Rol.objects.filter(id=self.rol.id).exists())

    def test_detalle_rol_ajax(self):
        self.client.login(username="admin", password="admin123")
        response = self.client.get(reverse("rol_detalle", args=[self.rol.id]))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["nombre"], self.rol.nombre)
        self.assertEqual(data["descripcion"], self.rol.descripcion)
        self.assertIn(self.permiso1.id, data["permisos"])
