from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta, date
from decimal import Decimal

from cliente_segmentacion.models import Segmentacion
from operaciones.models import Transaccion
from clientes.models import Cliente
from monedas.models import Moneda
from cotizaciones.models import TasaDeCambio
from metodos_pagos.models import MetodoPago
from usuarios.models import CustomUser
from django.contrib.auth.models import Group
from roles_permisos.models import GroupProfile

class AdminDashboardViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse('admin_dashboard')

        # Crear grupo ADMIN y perfil activo
        self.admin_group, _ = Group.objects.get_or_create(name='ADMIN')
        GroupProfile.objects.get_or_create(group=self.admin_group, estado="Activo")

        # Crear usuario y asignarle grupo ADMIN
        self.usuario = CustomUser.objects.create(username="admin", is_staff=True, is_superuser=True)
        self.usuario.groups.add(self.admin_group)
        self.client.force_login(self.usuario)

        # Crear monedas
        self.moneda_pyg = Moneda.objects.create(nombre='Guaraní', abreviacion='PYG')
        self.moneda_usd = Moneda.objects.create(nombre='Dólar', abreviacion='USD')

        # Crear segmentación y cliente
        self.segmentacion = Segmentacion.objects.create(nombre="Regular")
        self.cliente = Cliente.objects.create(nombre="Juan Pérez", estado="activo", segmentacion=self.segmentacion)

        # Crear método de pago
        self.metodo_pago, _ = MetodoPago.objects.get_or_create(nombre="Efectivo")

        # Crear tasa de cambio
        self.tasa = TasaDeCambio.objects.create(
            moneda_origen=self.moneda_pyg,
            moneda_destino=self.moneda_usd,
            precio_base=Decimal('7350.00'),
            comision_compra=Decimal('50.00'),
            comision_venta=Decimal('40.00'),
            vigencia=timezone.now(),
            estado=True
        )

        # **Fechas fijas para tests**
        self.fixed_today = date(2025, 11, 9)
        self.fixed_yesterday = self.fixed_today - timedelta(days=1)

        # Crear transacciones con fechas fijas
        self.tx_hoy = Transaccion.objects.create(
            cliente=self.cliente,
            moneda_origen=self.moneda_pyg,
            moneda_destino=self.moneda_usd,
            tipo="venta",
            ganancia=Decimal('500.00'),
            monto=Decimal('1000'),
            tasa_usada=self.tasa.monto_venta,
            tasa_ref=self.tasa,
            metodo_pago=self.metodo_pago,
            estado="confirmada",
            usuario=self.usuario,
            fecha=timezone.now()
        )

        self.tx_ayer = Transaccion.objects.create(
            cliente=self.cliente,
            moneda_origen=self.moneda_pyg,
            moneda_destino=self.moneda_usd,
            tipo="venta",
            ganancia=Decimal('300.00'),
            monto=Decimal('800'),
            tasa_usada=self.tasa.monto_venta,
            tasa_ref=self.tasa,
            metodo_pago=self.metodo_pago,
            estado="confirmada",
            usuario=self.usuario,
            fecha=timezone.now() - timedelta(days=1)
        )


    def test_dashboard_status_and_context(self):
        """La vista responde 200 y contiene claves principales."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        for key in ['ganancias_hoy', 'ganancias_ayer', 'clientes_activos',
                    'top_monedas', 'labels_ganancias_moneda',
                    'data_ganancias_moneda', 'tasas_evolucion',
                    'ganancia_total_rango']:
            self.assertIn(key, response.context)

    def test_ganancia_total_rango_filtrado(self):
        """Debe calcular correctamente la ganancia total del rango filtrado por moneda."""
        response = self.client.get(self.url, {'moneda': 'USD'})
        total = response.context['ganancia_total_rango']
        self.assertEqual(total, Decimal('800.00'))  # 500+300 si incluimos hoy y ayer

    def test_top_monedas_contains_usd(self):
        """Debe incluir USD en las monedas operadas del top."""
        response = self.client.get(self.url)
        monedas = response.context['labels_ganancias_moneda']
        self.assertIn('USD', monedas)

    def test_tasas_evolucion_incluye_usd(self):
        """Debe mostrar evolución de tasas para USD."""
        response = self.client.get(self.url)
        tasas = response.context['tasas_evolucion']
        self.assertIn('USD', tasas)
        self.assertTrue(len(tasas['USD']['compra']) > 0)
        self.assertTrue(len(tasas['USD']['venta']) > 0)
        
    def test_ganancias_hoy_y_ayer(self):
      """Calcula las ganancias de hoy y ayer según las transacciones actuales."""
      response = self.client.get(self.url)
      context = response.context

      # Sumar ganancias de transacciones según fechas reales
      hoy = timezone.localdate()
      ayer = hoy - timedelta(days=1)
      total_hoy = sum(tx.ganancia for tx in Transaccion.objects.filter(fecha__date=hoy))
      total_ayer = sum(tx.ganancia for tx in Transaccion.objects.filter(fecha__date=ayer))

      self.assertEqual(context['ganancias_hoy'], total_hoy)
      self.assertEqual(context['ganancias_ayer'], total_ayer)
