from django.test import TestCase, Client
from django.urls import reverse
from usuarios.models import CustomUser
from monedas.models import Moneda

class MonedaListViewTest(TestCase):
    def setUp(self):
        # Crear superusuario
        if not CustomUser.objects.filter(username='superadmin').exists():
            self.superadmin = CustomUser.objects.create_superuser(
                username='superadmin', email='admin@test.com', password='ContraseñaSegura123'
            )
        else:
            self.superadmin = CustomUser.objects.get(username='superadmin')
        self.client = Client()
        
        # Crear algunas monedas
        self.moneda1 = Moneda.objects.create(nombre='Dólar', abreviacion='USD', estado=True)
        self.moneda2 = Moneda.objects.create(nombre='Euro', abreviacion='EUR', estado=False)

    def test_lista_monedas_superadmin(self):
        # Login
        self.client.login(username='superadmin', password='ContraseñaSegura123')

        # Acceder a la vista de lista
        response = self.client.get(reverse('monedas'))
        self.assertEqual(response.status_code, 200)

        # Verificar que se muestren las monedas
        self.assertContains(response, 'Dólar')
        self.assertContains(response, 'Euro')

        # Verificar que los botones correctos aparezcan según el estado
        self.assertContains(response, 'Desactivar')  # moneda1
        self.assertContains(response, 'Activar')     # moneda2

    def test_busqueda_por_nombre(self):
        self.client.login(username='superadmin', password='ContraseñaSegura123')
        response = self.client.get(reverse('monedas'), {'q': 'Dólar', 'campo': 'nombre'})
        self.assertContains(response, 'Dólar')
        self.assertNotContains(response, 'Euro')
