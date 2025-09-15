from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from monedas.models import Moneda
from cotizaciones.models import TasaDeCambio

class TasaDeCambioListViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.guarani = Moneda.objects.create(nombre="Guaraní", abreviacion="PYG", estado=True)
        cls.dolar = Moneda.objects.create(nombre="Dólar", abreviacion="USD", estado=True)
        cls.euro = Moneda.objects.create(nombre="Euro", abreviacion="EUR", estado=True)

        # Crear varias tasas
        for i in range(15):
            TasaDeCambio.objects.create(
                moneda_origen=cls.guarani,
                moneda_destino=cls.dolar if i % 2 == 0 else cls.euro,
                monto_compra=100 + i,
                monto_venta=110 + i,
                vigencia=timezone.now(),
                estado=(i % 2 == 0)
            )
    def setUp(self):
        # Loguear antes de cada test
        self.client.login(username='superadmin', password='ContraseñaSegura123')

    def test_template_used_and_context(self):
        url = reverse('cotizacion')  # nombre de URL real
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'cotizaciones/lista.html')
        self.assertIn('tasas', response.context)
        self.assertTrue(len(response.context['tasas']) > 0)

    def test_list_contains_all_items(self):
        """Verifica que la lista traiga todas las tasas creadas"""
        url = reverse('cotizacion')
        response = self.client.get(url)
        self.assertEqual(len(response.context['tasas']), 15)

    def test_search_by_moneda_destino(self):
        url = reverse('cotizacion')
        response = self.client.get(url, {'campo': 'moneda_destino', 'q': 'USD'})
        self.assertEqual(response.status_code, 200)
        for tasa in response.context['tasas']:
            self.assertIn('USD', str(tasa.moneda_destino))

    def test_estado_activo_inactivo_display(self):
        url = reverse('cotizacion')
        response = self.client.get(url)
        self.assertContains(response, "Activo")
        self.assertContains(response, "Inactivo")
