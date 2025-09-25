from django.test import TestCase
from medio_acreditacion.models import TipoEntidadFinanciera, MedioAcreditacion
from medio_acreditacion.forms import TipoEntidadFinancieraForm, MedioAcreditacionForm
from clientes.models import Cliente
from monedas.models import Moneda
from cliente_segmentacion.models import Segmentacion

class TipoEntidadFinancieraFormTest(TestCase):
    def test_unique_nombre(self):
        TipoEntidadFinanciera.objects.create(nombre="Banco Test", tipo="BANCO", estado=True)
        form = TipoEntidadFinancieraForm(data={"nombre": "Banco Test", "tipo": "BANCO"})
        self.assertFalse(form.is_valid())
        self.assertIn("Ya existe una entidad con este nombre.", str(form.errors))

class MedioAcreditacionFormTest(TestCase):
    def test_unique_numero_cuenta(self):
        segmentacion = Segmentacion.objects.create(nombre="Segmento Test")
        cliente = Cliente.objects.create(nombre="Cliente Test", estado="activo", segmentacion=segmentacion)        
        entidad = TipoEntidadFinanciera.objects.create(nombre="Banco Test", tipo="BANCO", estado=True)
        moneda = Moneda.objects.create(nombre="Guaraní", estado=True)
        MedioAcreditacion.objects.create(
            cliente=cliente,
            entidad=entidad,
            numero_cuenta="123456",
            tipo_cuenta="AHORRO",
            titular="Titular Test",
            documento_titular="1234",
            moneda=moneda,
            estado=True
        )
        form = MedioAcreditacionForm(data={
            "cliente": cliente.id,
            "entidad": entidad.id,
            "numero_cuenta": "123456",
            "tipo_cuenta": "AHORRO",
            "titular": "Titular Test",
            "documento_titular": "1234",
            "moneda": moneda.id
        })
        self.assertFalse(form.is_valid())
        self.assertIn("Ya existe un medio de acreditación con el número", str(form.errors))
