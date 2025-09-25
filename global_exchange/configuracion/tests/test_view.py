from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import Group
from usuarios.models import CustomUser
from usuarios.forms import UserRolePermissionForm

class ConfiguracionViewsTestCase(TestCase):

    def setUp(self):
        self.client = Client()

        # Crear superusuario
        self.admin_user = CustomUser.objects.create_superuser(
            username="admin_user",
            email="admin@test.com",
            password="admin123",
            cedula="00000000000000000000",
            is_staff=True,
            is_active=True
        )

        # Crear grupo ADMIN y asignar al superusuario
        admin_group, _ = Group.objects.get_or_create(name='ADMIN')
        self.admin_user.groups.add(admin_group)

        # Crear usuarios normales
        self.user1 = CustomUser.objects.create_user(
            username="user1",
            email="user1@test.com",
            password="user123",
            cedula="11111111111111111111",
            is_active=True
        )
        self.user2 = CustomUser.objects.create_user(
            username="user2",
            email="user2@test.com",
            password="user123",
            cedula="22222222222222222222",
            is_active=True
        )

        # Crear roles/grupos
        self.group1 = Group.objects.create(name="Group1")
        self.group2 = Group.objects.create(name="Group2")

        # Login del admin
        self.client.force_login(self.admin_user)


    def test_configuracion_view(self):
        response = self.client.get(reverse('configuracion'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'configuracion_home.html')
