from django.test import TestCase
from django.contrib.auth.models import Group
from roles_permisos.models import GroupProfile

class GroupProfileModelTest(TestCase):

    def test_group_profile_str(self):
        group = Group.objects.create(name="Test Group")
        profile = GroupProfile.objects.create(group=group, estado="Activo")

        self.assertEqual(str(profile), "Test Group (Activo)")
        self.assertEqual(profile.estado, "Activo")
        self.assertEqual(profile.group.name, "Test Group")
