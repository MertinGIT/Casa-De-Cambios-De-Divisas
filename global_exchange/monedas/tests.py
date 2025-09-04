from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Moneda


class MonedaModelTest(TestCase):
    def test_str_representation(self):
        moneda = Moneda.objects.create(nombre="Guaraní", abreviacion="PYG")
        self.assertEqual(str(moneda), "Guaraní")


class MonedaViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = get_user_model().objects.create_user(
            username="admin", password="12345", is_superuser=True
        )
        self.client.login(username="admin", password="12345")
        self.moneda = Moneda.objects.create(nombre="Dólar", abreviacion="USD")

    def test_moneda_lista(self):
        response = self.client.get(reverse("monedas"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Dólar")

    def test_moneda_nueva_post_valid(self):
        response = self.client.post(reverse("moneda_nueva"), {
            "nombre": "Euro",
            "abreviacion": "EUR",
            "estado": True
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Moneda.objects.filter(nombre="Euro").exists())

    def test_moneda_nueva_post_invalid(self):
        response = self.client.post(reverse("moneda_nueva"), {
            "nombre": "",
            "abreviacion": "EUR",
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "show_modal")

    def test_moneda_editar_post_valid(self):
        response = self.client.post(reverse("moneda_editar", args=[self.moneda.id]), {
            "nombre": "Dólar Americano",
            "abreviacion": "USD",
            "estado": True
        })
        self.assertEqual(response.status_code, 302)
        self.moneda.refresh_from_db()
        self.assertEqual(self.moneda.nombre, "Dólar Americano")

    def test_moneda_editar_post_invalid(self):
        response = self.client.post(reverse("moneda_editar", args=[self.moneda.id]), {
            "nombre": "",
            "abreviacion": "USD",
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "show_modal")

    def test_moneda_eliminar(self):
        response = self.client.post(reverse("moneda_eliminar", args=[self.moneda.id]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Moneda.objects.filter(id=self.moneda.id).exists())

    def test_moneda_detalle(self):
        response = self.client.get(reverse("moneda_detalle", args=[self.moneda.id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["abreviacion"], "USD")
