from django.test import TestCase
from medio_acreditacion.models import TipoEntidadFinanciera, MedioAcreditacion
from clientes.models import Cliente
from monedas.models import Moneda
from cliente_segmentacion.models import Segmentacion

class TipoEntidadFinancieraModelTest(TestCase):
    def test_unique_nombre(self):
        TipoEntidadFinanciera.objects.create(nombre="Banco Test", tipo="BANCO", estado=True)
        self.assertEqual(TipoEntidadFinanciera.objects.filter(nombre="Banco Test").count(), 1)

class MedioAcreditacionModelTest(TestCase):
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
        self.assertEqual(MedioAcreditacion.objects.filter(numero_cuenta="123456").count(), 1)
