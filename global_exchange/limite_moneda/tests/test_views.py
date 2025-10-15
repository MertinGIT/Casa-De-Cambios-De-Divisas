from django.test import TestCase, Client
from django.urls import reverse
from decimal import Decimal
from monedas.models import Moneda
from limite_moneda.models import LimiteTransaccion
from usuarios.models import CustomUser


class LimiteMonedaViewsTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.superadmin = CustomUser.objects.get(username='superadmin')
        cls.pyg = Moneda.objects.create(
            nombre="Guaraní",
            abreviacion="PYG",
            estado=True
        )
        cls.limite = LimiteTransaccion.objects.create(
            limite_diario=Decimal("10000.00"),
            limite_mensual=Decimal("100000.00"),
            estado="activo"
        )

    def setUp(self):
        self.client = Client()
        self.client.login(username='superadmin', password='ContraseñaSegura123')

    def test_lista_limites_view(self):
        """Verifica que la lista de límites carga correctamente"""
        url = reverse("lista-limites")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("limites", response.context)

    def test_editar_limite_post_valido(self):
        """Verifica que se puede editar un límite"""
        url = reverse("limite-editar", args=[self.limite.id])
        data = {
            "limite_diario": "15000.00",
            "limite_mensual": "150000.00",
            "estado": "activo",
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        self.limite.refresh_from_db()
        self.assertEqual(self.limite.limite_diario, Decimal("15000.00"))

    def test_limite_detalle_json(self):
        """Verifica que devuelve JSON con detalles del límite"""
        url = reverse("limite-detalle", args=[self.limite.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertEqual(json_data["id"], self.limite.id)

    def test_cambiar_estado_limite(self):
        """Verifica que cambia el estado del límite"""
        self.assertEqual(self.limite.estado, "activo")
        url = reverse("limite-cambiar-estado", args=[self.limite.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.limite.refresh_from_db()
        self.assertEqual(self.limite.estado, "inactivo")