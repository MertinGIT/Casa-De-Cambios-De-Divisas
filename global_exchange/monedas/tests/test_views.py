from django.test import TestCase, Client
from django.urls import reverse
from monedas.models import Moneda
from usuarios.models import CustomUser 
class MonedaViewsTest(TestCase):
    def setUp(self):
        self.superadmin = CustomUser.objects.create_superuser(username='admin', email='admin@test.com', password='1234')
        self.client = Client()
        self.moneda = Moneda.objects.create(nombre='Dólar', abreviacion='USD')

    def test_lista_vista_superadmin(self):
        self.client.login(username='admin', password='1234')
        response = self.client.get(reverse('monedas'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Dólar')
        # Esto fallará porque no hay moneda llamada 'Yen'
        #self.assertContains(response, 'Yen')        

    def test_crear_moneda(self):
        self.client.login(username='admin', password='1234')
        data = {'nombre': 'Euro', 'abreviacion': 'EUR'}
        response = self.client.post(reverse('moneda_nueva'), data)
        self.assertRedirects(response, reverse('monedas'))
        self.assertTrue(Moneda.objects.filter(nombre='Euro').exists())

    def test_editar_moneda(self):
        self.client.login(username='admin', password='1234')
        data = {'nombre': 'Dólar Editado', 'abreviacion': 'USD'}
        response = self.client.post(reverse('moneda_editar', args=[self.moneda.id]), data)
        self.assertRedirects(response, reverse('monedas'))
        self.moneda.refresh_from_db()
        self.assertEqual(self.moneda.nombre, 'Dólar Editado')

    def test_desactivar_moneda(self):
        self.client.login(username='admin', password='1234')
        response = self.client.get(reverse('moneda_desactivar', args=[self.moneda.id]))
        self.assertRedirects(response, reverse('monedas'))
        self.moneda.refresh_from_db()
        self.assertFalse(self.moneda.estado)

    def test_detalle_json(self):
        self.client.login(username='admin', password='1234')
        response = self.client.get(reverse('moneda_detalle', args=[self.moneda.id]))
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content,
            {"id": self.moneda.id, "nombre": self.moneda.nombre, "abreviacion": self.moneda.abreviacion}
        )
