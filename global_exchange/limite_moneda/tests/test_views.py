# limite_moneda/tests/test_views.py
from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from limite_moneda.models import LimiteTransaccion

class LimiteTransaccionViewsTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.limite = LimiteTransaccion.objects.create(
            # cliente eliminado
            limite_diario=Decimal("1000000.00"),
            limite_mensual=Decimal("10000000.00"),
            estado="activo",
        )

    def test_crear_limite(self):
        data = {
            # 'cliente': <eliminado>,
            'limite_diario': '2000000.00',
            'limite_mensual': '15000000.00',
            'estado': 'activo',
        }
        resp = self.client.post(reverse('limite_crear'), data, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(LimiteTransaccion.objects.filter(
            limite_diario=Decimal('2000000.00'),
            limite_mensual=Decimal('15000000.00')
        ).exists())

    def test_editar_limite(self):
        data = {
            # 'cliente': <eliminado>,
            'limite_diario': '3000000.00',
            'limite_mensual': '20000000.00',
            'estado': 'activo',
        }
        resp = self.client.post(reverse('limite_editar', args=[self.limite.id]), data, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.limite.refresh_from_db()
        self.assertEqual(self.limite.limite_diario, Decimal('3000000.00'))
        self.assertEqual(self.limite.limite_mensual, Decimal('20000000.00'))
