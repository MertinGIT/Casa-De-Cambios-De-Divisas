from django.test import TestCase, Client
from django.urls import reverse
from metodos_pagos.models import MetodoPago
from usuarios.models import CustomUser

class MetodoPagoViewsTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Obtener el superusuario existente
        cls.user = CustomUser.objects.get(username='superadmin')

        # Crear un método de pago inicial
        cls.metodo = MetodoPago.objects.create(
            nombre='Tarjeta Crédito',
            descripcion='Pago con tarjeta',
            activo=True
        )

    def setUp(self):
        # Client y login para cada test
        self.client = Client()
        self.client.login(username='superadmin', password='ContraseñaSegura123')

    def test_lista_metodos_pagos(self):
        url = reverse('metodos_pagos')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.metodo.nombre)

    def test_crear_metodo_pago(self):
        url = reverse('metodos-pagos-agregar')
        data = {'nombre': 'Transferencia', 'descripcion': 'Pago por transferencia', 'activo': True}
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(MetodoPago.objects.filter(nombre='Transferencia').exists())

    def test_editar_metodo_pago(self):
        url = reverse('metodos-pagos-editar', args=[self.metodo.id])
        data = {'nombre': 'Tarjeta Débito', 'descripcion': self.metodo.descripcion, 'activo': self.metodo.activo}
        response = self.client.post(url, data, follow=True)
        self.metodo.refresh_from_db()
        self.assertEqual(self.metodo.nombre, 'Tarjeta Débito')
        self.assertEqual(response.status_code, 200)

    def test_desactivar_metodo_pago(self):
        url = reverse('metodos-pagos-desactivate', args=[self.metodo.id])
        response = self.client.post(url, follow=True)
        self.metodo.refresh_from_db()
        self.assertFalse(self.metodo.activo)
        self.assertEqual(response.status_code, 200)

    def test_activar_metodo_pago(self):
        self.metodo.activo = False
        self.metodo.save()
        url = reverse('metodos-pagos-activate', args=[self.metodo.id])
        response = self.client.post(url, follow=True)
        self.metodo.refresh_from_db()
        self.assertTrue(self.metodo.activo)
        self.assertEqual(response.status_code, 200)
    