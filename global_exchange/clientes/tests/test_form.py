from django.test import TestCase
from clientes.forms import ClienteForm
from clientes.models import Cliente
from cliente_segmentacion.models import Segmentacion

class ClienteFormTest(TestCase):

    def setUp(self):
        # Crear segmentaciones de prueba
        self.segment_activa = Segmentacion.objects.create(nombre="VIP", estado="activo")
        self.segment_inactiva = Segmentacion.objects.create(nombre="Básica", estado="inactivo")

        # Crear cliente existente para test de email único
        self.cliente_existente = Cliente.objects.create(
            nombre="Juan Perez",
            email="juan@example.com",
            segmentacion=self.segment_activa
        )

    def test_form_valido(self):
        """Formulario válido con datos correctos"""
        data = {
            "nombre": "Maria Lopez",
            "email": "maria@example.com",
            "telefono": "098112233",
            "segmentacion": self.segment_activa.id,
            "estado": "activo"
        }
        form = ClienteForm(data=data)
        self.assertTrue(form.is_valid())

    def test_nombre_obligatorio(self):
        """El nombre es obligatorio y mínimo 3 caracteres"""
        data = {
            "nombre": "",
            "email": "nuevo@example.com",
            "segmentacion": self.segment_activa.id
        }
        form = ClienteForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("nombre", form.errors)

        data["nombre"] = "Al"
        form = ClienteForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("nombre", form.errors)

    def test_email_obligatorio_y_unico(self):
        """El email es obligatorio y no puede repetirse"""
        # Email vacío
        data = {
            "nombre": "Nuevo Cliente",
            "email": "",
            "segmentacion": self.segment_activa.id
        }
        form = ClienteForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

        # Email duplicado
        data["email"] = "juan@example.com"
        form = ClienteForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

    def test_segmentacion_obligatoria_activa(self):
        """La segmentación es obligatoria y debe ser activa"""
        # Sin segmentación
        data = {
            "nombre": "Cliente Test",
            "email": "test@example.com"
        }
        form = ClienteForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("segmentacion", form.errors)

        # Segmentación inactiva no debería estar disponible en queryset
        form = ClienteForm()
        self.assertNotIn(self.segment_inactiva, form.fields["segmentacion"].queryset)

    def test_edicion_cliente_permite_mismo_email(self):
        """Al editar un cliente, permite mantener el mismo email"""
        cliente = self.cliente_existente
        data = {
            "nombre": "Juan Perez",
            "email": "juan@example.com",
            "segmentacion": self.segment_activa.id
        }
        form = ClienteForm(data=data, instance=cliente)
        self.assertTrue(form.is_valid())