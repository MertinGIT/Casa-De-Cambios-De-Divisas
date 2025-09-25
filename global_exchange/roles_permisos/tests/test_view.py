from django.test import TestCase
from django.contrib.auth.models import Group, Permission
from roles_permisos.forms import RolForm

class RolFormTest(TestCase):

    def test_rol_form_valid(self):
        permiso = Permission.objects.first()
        group = Group(name="Nuevo Rol")
        form_data = {"name": "Nuevo Rol", "permisos": [permiso.id]}
        form = RolForm(data=form_data, instance=group)

        self.assertTrue(form.is_valid())
        saved_group = form.save()
        self.assertEqual(saved_group.name, "Nuevo Rol")
        self.assertIn(permiso, saved_group.permissions.all())

    def test_rol_form_invalid(self):
        form = RolForm(data={"name": ""})  # nombre vacío
        self.assertFalse(form.is_valid())
        self.assertIn("name", form.errors)
