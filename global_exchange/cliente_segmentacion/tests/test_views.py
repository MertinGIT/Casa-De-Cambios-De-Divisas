from django.test import TestCase, Client
from django.urls import reverse
from clientes.models import Segmentacion
from django.contrib.auth import get_user_model
import json

User = get_user_model()

class SegmentacionViewsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.superuser = User.objects.create_superuser(
            username="admin",
            email="admin@test.com",
            password="password"
        )
        self.segmentacion = Segmentacion.objects.create(
            nombre="VIP",
            descripcion="Cliente VIP",
            descuento=20,
            estado="activo"
        )

    def test_lista_segmentaciones_requiere_superuser(self):
        response = self.client.get(reverse("lista-segmentaciones"))
        self.assertEqual(response.status_code, 302)

        self.client.force_login(self.superuser)
        response = self.client.get(reverse("lista-segmentaciones"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "VIP")

    def test_crear_segmentacion_post_normal(self):
        self.client.force_login(self.superuser)
        response = self.client.post(
            reverse("segmentaciones-agregar"),
            {
                "nombre": "Premium",
                "descripcion": "Cliente Premium",
                "descuento": 15,
                "estado": "activo"
            }
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Segmentacion.objects.filter(nombre="Premium").exists())

    def test_crear_segmentacion_post_ajax(self):
        self.client.force_login(self.superuser)
        response = self.client.post(
            reverse("segmentaciones-agregar"),
            {
                "nombre": "Gold",
                "descripcion": "Cliente Gold",
                "descuento": 10,
                "estado": "activo"
            },
            HTTP_X_REQUESTED_WITH="XMLHttpRequest"
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data["success"])
        self.assertEqual(data["segmentacion"]["nombre"], "Gold")

    def test_editar_segmentacion_post(self):
        self.client.force_login(self.superuser)
        url = reverse("segmentaciones-editar", args=[self.segmentacion.id])
        response = self.client.post(
            url,
            {
                "nombre": "VIP Actualizado",
                "descripcion": "Cliente VIP Modificado",
                "descuento": 25,
                "estado": "activo"
            }
        )
        self.segmentacion.refresh_from_db()
        self.assertEqual(self.segmentacion.nombre, "VIP Actualizado")
        self.assertEqual(self.segmentacion.descuento, 25)

    def test_cambiar_estado_segmentacion(self):
        self.client.force_login(self.superuser)
        url = reverse("segmentaciones-state", args=[self.segmentacion.id])
        response = self.client.post(url, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.segmentacion.refresh_from_db()
        self.assertEqual(self.segmentacion.estado, "inactivo")
        data = json.loads(response.content)
        self.assertTrue(data["success"])
        self.assertEqual(data["nuevo_estado"], "inactivo")

    def test_segmentacion_detalle(self):
        self.client.force_login(self.superuser)
        url = reverse("segmentacion-detalle", args=[self.segmentacion.id])
        response = self.client.get(url)
        data = json.loads(response.content)
        self.assertEqual(data["nombre"], "VIP")
        self.assertEqual(data["descuento"], float(self.segmentacion.descuento))
