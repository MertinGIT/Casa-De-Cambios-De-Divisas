# tests/test_views.py
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
User = get_user_model()
from clientes.models import Cliente, Segmentacion

class ClienteViewsTest(TestCase):
    def setUp(self):
        # Usa el superadmin que ya existe en la BD
        self.superuser = User.objects.get(username="superadmin")
        self.client.force_login(self.superuser)

        self.segmento = Segmentacion.objects.create(nombre="VIP")
        self.cliente = Cliente.objects.create(
            nombre="Juan Pérez",
            email="juan@example.com",
            telefono="123456",
            segmentacion=self.segmento,
            estado="activo"
        )

    def test_clientes_template_render(self):
        response = self.client.get(reverse("clientes"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "clientes/lista.html")

    def test_listview_muestra_clientes(self):
        response = self.client.get(reverse("clientes"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Juan Pérez")

    def test_listview_filtrado_por_nombre(self):
        response = self.client.get(reverse("clientes"), {"q": "Juan", "campo": "nombre"})
        self.assertContains(response, "Juan Pérez")
        response = self.client.get(reverse("clientes"), {"q": "Otro", "campo": "nombre"})
        self.assertNotContains(response, "Juan Pérez")

    def test_listview_filtrado_por_segmento(self):
        response = self.client.get(reverse("clientes"), {"q": "VIP", "campo": "segmento"})
        self.assertContains(response, "Juan Pérez")

    def test_create_cliente(self):
        data = {
            "nombre": "Ana Gómez",
            "email": "ana@example.com",
            "telefono": "987654",
            "segmentacion": self.segmento.id,
            "estado": "activo",
        }
        response = self.client.post(reverse("clientes-agregar"), data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Cliente.objects.filter(email="ana@example.com").exists())

    def test_update_cliente(self):
        data = {
            "nombre": "Juan Editado",
            "email": "juan@example.com",
            "telefono": "555",
            "segmentacion": self.segmento.id,
            "estado": "activo",
        }
        response = self.client.post(reverse("clientes-editar", args=[self.cliente.id]), data)
        self.assertEqual(response.status_code, 302)
        self.cliente.refresh_from_db()
        self.assertEqual(self.cliente.nombre, "Juan Editado")

    def test_delete_cliente(self):
        response = self.client.post(reverse("clientes-eliminar", args=[self.cliente.id]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Cliente.objects.filter(id=self.cliente.id).exists())

    def test_desactivar_cliente(self):
        response = self.client.post(reverse("clientes-desactivate", args=[self.cliente.id]))
        self.assertEqual(response.status_code, 302)
        self.cliente.refresh_from_db()
        self.assertEqual(self.cliente.estado, "inactivo")

    def test_activar_cliente(self):
        self.cliente.estado = "inactivo"
        self.cliente.save()
        response = self.client.post(reverse("clientes-activate", args=[self.cliente.id]))
        self.assertEqual(response.status_code, 302)
        self.cliente.refresh_from_db()
        self.assertEqual(self.cliente.estado, "activo")

    def test_check_email_existente(self):
        response = self.client.post(reverse("clientes-check-email"), {"email": "juan@example.com"})
        self.assertJSONEqual(response.content, "false")

    def test_check_email_disponible(self):
        response = self.client.post(reverse("clientes-check-email"), {"email": "nuevo@example.com"})
        self.assertJSONEqual(response.content, "true")

    def test_cliente_detalle(self):
        response = self.client.get(reverse("clientes-detalle", args=[self.cliente.id]))
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content,
            {
                "cedula": None,
                "nombre": "Juan Pérez",
                "email": "juan@example.com",
                "telefono": "123456",
                "segmentacion": self.segmento.id,
                "estado": "activo",
            },
        )