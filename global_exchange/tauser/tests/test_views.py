from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import Group
from decimal import Decimal

from usuarios.models import CustomUser
from clientes.models import Cliente, SaldoCliente
from cliente_usuario.models import Usuario_Cliente
from cliente_segmentacion.models import Segmentacion
from tauser.models import Localidad, Denominacion, StockTauser
from monedas.models import Moneda
from medio_acreditacion.models import MedioAcreditacion, TipoEntidadFinanciera


class TauserViewsTest(TestCase):
    """Tests para las vistas del módulo TAUSER"""

    def setUp(self):
        """Configuración inicial"""
        # Crear grupo
        self.grupo = Group.objects.create(name="Usuarios ATM")
        
        # Crear usuario
        self.user = CustomUser.objects.create_user(
            username="usuario_atm",
            email="atm@test.com",
            password="password123",
            cedula="1234567"
        )
        self.user.groups.add(self.grupo)
        
        # Crear segmentación
        self.segmentacion = Segmentacion.objects.create(
            nombre="Segmentación Test"
        )
        
        # Crear cliente
        self.cliente = Cliente.objects.create(
            nombre="Cliente Test",
            ruc="80012345-6",
            cedula="1234567",
            email="test@test.com",
            segmentacion=self.segmentacion,
            estado="activo"
        )
        
        # Asociar usuario-cliente
        Usuario_Cliente.objects.create(
            id_usuario=self.user,
            id_cliente=self.cliente
        )
        
        # Crear localidad
        self.localidad = Localidad.objects.create(
            nombre="Sucursal Test",
            direccion="Test",
            activo=True
        )
        
        # Crear monedas
        self.moneda_pyg = Moneda.objects.create(
            nombre="Guaraní",
            abreviacion="PYG",
            estado=True
        )
        
        self.moneda_usd = Moneda.objects.create(
            nombre="Dólar",
            abreviacion="USD",
            estado=True
        )
        
        # Crear denominación y stock
        self.denominacion = Denominacion.objects.create(
            moneda=self.moneda_pyg,
            valor=Decimal("100000.00"),
            activo=True
        )
        
        self.stock = StockTauser.objects.create(
            localidad=self.localidad,
            denominacion=self.denominacion,
            cantidad=50,
            cantidad_minima=10
        )
        
        # Crear entidad Tauser
        self.entidad = TipoEntidadFinanciera.objects.create(
            nombre="Tauser",
            tipo="billetera_digital",
            estado=True
        )
        
        # Crear medio de acreditación
        self.medio = MedioAcreditacion.objects.create(
            cliente=self.cliente,
            entidad=self.entidad,
            localidad=self.localidad,
            estado=True
        )
        
        # Crear saldos
        SaldoCliente.objects.create(
            cliente=self.cliente,
            moneda=self.moneda_pyg,
            localidad=self.localidad,
            saldo=Decimal("1000000.00")
        )
        
        SaldoCliente.objects.create(
            cliente=self.cliente,
            moneda=self.moneda_usd,
            localidad=self.localidad,
            saldo=Decimal("100.00")
        )
        
        self.client = Client()

    def test_seleccionar_localidad_get(self):
        """Test: Acceder a selección de localidad"""
        url = reverse('atm_seleccionar_localidad')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('localidades', response.context)

    def test_seleccionar_localidad_post(self):
        """Test: Seleccionar localidad exitosamente"""
        url = reverse('atm_seleccionar_localidad')
        response = self.client.post(url, {'localidad_id': self.localidad.id})
        
        self.assertRedirects(response, reverse('atm_login'))
        self.assertEqual(self.client.session['atm_localidad_id'], self.localidad.id)

    def test_login_atm_exitoso(self):
        """Test: Login exitoso en el ATM"""
        # Configurar sesión de localidad
        session = self.client.session
        session['atm_localidad_id'] = self.localidad.id
        session.save()
        
        url = reverse('atm_login')
        response = self.client.post(url, {
            'cedula': '1234567',
            'password': 'password123'
        })
        
        self.assertRedirects(response, reverse('atm_seleccionar_cliente'))
        self.assertEqual(self.client.session['atm_user_id'], self.user.id)

    def test_seleccionar_cliente_exitoso(self):
        """Test: Seleccionar cliente exitosamente"""
        session = self.client.session
        session['atm_localidad_id'] = self.localidad.id
        session['atm_user_id'] = self.user.id
        session['is_atm_session'] = True
        session.save()
        
        url = reverse('atm_seleccionar_cliente')
        response = self.client.post(url, {'cliente_id': self.cliente.id})
        
        self.assertRedirects(response, reverse('atm_dashboard'))
        self.assertEqual(self.client.session['atm_cliente_id'], self.cliente.id)

    def test_dashboard_con_sesion_completa(self):
        """Test: Acceder al dashboard con sesión completa"""
        session = self.client.session
        session['atm_localidad_id'] = self.localidad.id
        session['atm_user_id'] = self.user.id
        session['atm_cliente_id'] = self.cliente.id
        session['is_atm_session'] = True
        session.save()
        
        url = reverse('atm_dashboard')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('cliente', response.context)

    def test_depositar_get(self):
        """Test: Acceder a la página de depósito"""
        session = self.client.session
        session['atm_localidad_id'] = self.localidad.id
        session['atm_user_id'] = self.user.id
        session['atm_cliente_id'] = self.cliente.id
        session['is_atm_session'] = True
        session.save()
        
        url = reverse('atm_depositar')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)

    def test_depositar_post_sin_datos(self):
        """Test: Intentar depositar sin datos"""
        session = self.client.session
        session['atm_localidad_id'] = self.localidad.id
        session['atm_user_id'] = self.user.id
        session['atm_cliente_id'] = self.cliente.id
        session['is_atm_session'] = True
        session.save()
        
        url = reverse('atm_depositar')
        response = self.client.post(url, {})
        
        # Debe retornar 200 con errores o redirigir de vuelta
        self.assertIn(response.status_code, [200, 302])

    def test_extraer_get(self):
        """Test: Acceder a la página de extracción"""
        session = self.client.session
        session['atm_localidad_id'] = self.localidad.id
        session['atm_user_id'] = self.user.id
        session['atm_cliente_id'] = self.cliente.id
        session['is_atm_session'] = True
        session.save()
        
        url = reverse('atm_extraer')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)

    def test_transacciones(self):
        """Test: Ver historial de transacciones"""
        session = self.client.session
        session['atm_localidad_id'] = self.localidad.id
        session['atm_user_id'] = self.user.id
        session['atm_cliente_id'] = self.cliente.id
        session['is_atm_session'] = True
        session.save()
        
        url = reverse('atm_transacciones')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)

    def test_logout_atm(self):
        """Test: Cerrar sesión del ATM"""
        session = self.client.session
        session['atm_localidad_id'] = self.localidad.id
        session['atm_user_id'] = self.user.id
        session['atm_cliente_id'] = self.cliente.id
        session['is_atm_session'] = True
        session.save()
        
        url = reverse('atm_logout')
        response = self.client.get(url)
        
        self.assertRedirects(response, reverse('atm_seleccionar_localidad'))
        self.assertNotIn('atm_user_id', self.client.session)