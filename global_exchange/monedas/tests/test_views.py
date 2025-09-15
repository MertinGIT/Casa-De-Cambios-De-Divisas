from django.test import TestCase, Client
from django.urls import reverse
from monedas.models import Moneda
from usuarios.models import CustomUser
from django.contrib.auth.models import Permission

class MonedaViewsTest(TestCase):
    def setUp(self):
        self.client = Client()

        # Verificar si el superusuario ya existe
        if not CustomUser.objects.filter(username='superadmin').exists():
            self.supersuperadmin = CustomUser.objects.create_superuser(
                username='superadmin',
                email='superadmin@test.com',
                password='ContraseñaSegura123',
                is_staff=True,
                is_active=True
            )
        else:
            self.supersuperadmin = CustomUser.objects.get(username='superadmin')

        # Asegurarnos de que tenga permisos para todas las acciones de Moneda
        permisos = Permission.objects.filter(content_type__app_label='monedas')
        self.supersuperadmin.user_permissions.set(permisos)
        self.supersuperadmin.save()

        # Crear una moneda de prueba
        self.moneda = Moneda.objects.create(nombre='Dólar', abreviacion='USD')

    def test_lista_vista_supersuperadmin(self):
        self.client.login(username='superadmin', password='ContraseñaSegura123')
        response = self.client.get(reverse('monedas'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Dólar')

    def test_crear_moneda(self):
        self.client.login(username='superadmin', password='ContraseñaSegura123')
        data = {'nombre': 'Euro', 'abreviacion': 'EUR'}
        response = self.client.post(reverse('moneda_nueva'), data)
        self.assertRedirects(response, reverse('monedas'))
        self.assertTrue(Moneda.objects.filter(nombre='Euro').exists())

    def test_editar_moneda(self):
        self.client.login(username='superadmin', password='ContraseñaSegura123')
        data = {'nombre': 'Dólar Editado', 'abreviacion': 'USD'}
        response = self.client.post(reverse('moneda_editar', args=[self.moneda.id]), data)
        self.assertRedirects(response, reverse('monedas'))
        self.moneda.refresh_from_db()
        self.assertEqual(self.moneda.nombre, 'Dólar Editado')

    def test_desactivar_moneda(self):
        self.client.login(username='superadmin', password='ContraseñaSegura123')
        response = self.client.get(reverse('moneda_desactivar', args=[self.moneda.id]))
        self.assertRedirects(response, reverse('monedas'))
        self.moneda.refresh_from_db()
        self.assertFalse(self.moneda.estado)

    def test_detalle_json(self):
        self.client.login(username='superadmin', password='ContraseñaSegura123')
        response = self.client.get(reverse('moneda_detalle', args=[self.moneda.id]))
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content,
            {"id": self.moneda.id, "nombre": self.moneda.nombre, "abreviacion": self.moneda.abreviacion}
        )
