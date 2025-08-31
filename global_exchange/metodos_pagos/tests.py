"""
Tests para la aplicación de métodos de pago
Ejecutar con: python manage.py test metodos_pagos.tests
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.http import JsonResponse
import json
from .models import MetodoPago
from .forms import MetodoPagoForm


class MetodoPagoModelTests(TestCase):
    """Tests para el modelo MetodoPago"""
    
    def setUp(self):
        """Configuración inicial para cada test"""
        self.metodo_pago = MetodoPago.objects.create(
            nombre="Tarjeta de Crédito",
            descripcion="Pagos con tarjeta de crédito",
            activo=True
        )
    
    def test_crear_metodo_pago(self):
        """Test creación básica de método de pago"""
        metodo = MetodoPago.objects.create(
            nombre="PayPal",
            descripcion="Pagos en línea",
            activo=True
        )
        self.assertEqual(metodo.nombre, "PayPal")
        self.assertEqual(metodo.descripcion, "Pagos en línea")
        self.assertTrue(metodo.activo)
        self.assertEqual(str(metodo), "PayPal")
    
    def test_metodo_pago_activo_false_por_defecto(self):
        """Test que activo sea False por defecto"""
        metodo = MetodoPago.objects.create(nombre="Efectivo")
        self.assertFalse(metodo.activo)
    
    def test_nombre_unico_case_sensitive(self):
        """Test que el nombre debe ser único (case sensitive a nivel DB)"""
        with self.assertRaises(IntegrityError):
            MetodoPago.objects.create(nombre="Tarjeta de Crédito")
    
    def test_descripcion_opcional(self):
        """Test que descripción es opcional"""
        metodo = MetodoPago.objects.create(nombre="Efectivo")
        self.assertIsNone(metodo.descripcion)
    
    def test_ordenamiento_por_nombre(self):
        """Test que el modelo se ordena por nombre"""
        MetodoPago.objects.create(nombre="Efectivo")
        MetodoPago.objects.create(nombre="Bitcoin")
        
        metodos = list(MetodoPago.objects.all())
        nombres = [m.nombre for m in metodos]
        self.assertEqual(nombres, ["Bitcoin", "Efectivo", "Tarjeta de Crédito"])


class MetodoPagoFormTests(TestCase):
    """Tests para el formulario MetodoPagoForm"""
    
    def setUp(self):
        """Configuración inicial para cada test"""
        self.metodo_existente = MetodoPago.objects.create(
            nombre="Tarjeta de Crédito",
            descripcion="Pagos con tarjeta"
        )
    
    def test_formulario_valido(self):
        """Test formulario con datos válidos"""
        form_data = {
            'nombre': 'PayPal',
            'descripcion': 'Pagos en línea'
        }
        form = MetodoPagoForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_nombre_requerido(self):
        """Test que nombre es requerido"""
        form_data = {'descripcion': 'Test'}
        form = MetodoPagoForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('nombre', form.errors)
        self.assertIn('obligatorio', str(form.errors['nombre']))
    
    def test_nombre_vacio(self):
        """Test nombre vacío o solo espacios"""
        form_data = {'nombre': '   '}
        form = MetodoPagoForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('obligatorio', str(form.errors['nombre']))
    
    def test_nombre_muy_corto(self):
        """Test nombre con menos de 3 caracteres"""
        form_data = {'nombre': 'AB'}
        form = MetodoPagoForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('3 caracteres', str(form.errors['nombre']))
    
    def test_nombre_muy_largo(self):
        """Test nombre con más de 100 caracteres"""
        form_data = {'nombre': 'A' * 101}
        form = MetodoPagoForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('100 caracteres', str(form.errors['nombre']))
    
    def test_nombre_duplicado_case_insensitive(self):
        """Test que no permite nombres duplicados (case insensitive)"""
        form_data = {'nombre': 'TARJETA DE CRÉDITO'}  # Mismo nombre en mayúsculas
        form = MetodoPagoForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('ya existe', str(form.errors['nombre']))
    
    def test_nombre_duplicado_con_espacios(self):
        """Test nombre duplicado con espacios extra"""
        form_data = {'nombre': '  Tarjeta de Crédito  '}
        form = MetodoPagoForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('ya existe', str(form.errors['nombre']))
    
    def test_edicion_mismo_nombre(self):
        """Test que permite editar manteniendo el mismo nombre"""
        form_data = {
            'nombre': 'Tarjeta de Crédito',
            'descripcion': 'Nueva descripción'
        }
        form = MetodoPagoForm(data=form_data, instance=self.metodo_existente)
        self.assertTrue(form.is_valid())
    
    def test_descripcion_opcional(self):
        """Test que descripción es opcional"""
        form_data = {'nombre': 'Efectivo'}
        form = MetodoPagoForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_descripcion_muy_larga(self):
        """Test descripción con más de 500 caracteres"""
        form_data = {
            'nombre': 'PayPal',
            'descripcion': 'A' * 501
        }
        form = MetodoPagoForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('500 caracteres', str(form.errors['descripcion']))
    
    def test_normalizacion_texto(self):
        """Test que el texto se normaliza correctamente"""
        form_data = {'nombre': '  PayPal  '}
        form = MetodoPagoForm(data=form_data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['nombre'], 'PayPal')


class MetodoPagoViewTests(TestCase):
    """Tests para las vistas de MetodoPago"""
    
    def setUp(self):
        """Configuración inicial para cada test"""
        self.client = Client()
        # Crear superusuario
        self.superuser = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='testpass123'
        )
        # Crear usuario normal
        self.user = User.objects.create_user(
            username='user',
            email='user@test.com', 
            password='testpass123'
        )
        # Crear método de pago de prueba
        self.metodo_pago = MetodoPago.objects.create(
            nombre="Tarjeta de Crédito",
            descripcion="Pagos con tarjeta"
        )
    
    def test_acceso_sin_autenticar(self):
        """Test que redirige a login si no está autenticado"""
        response = self.client.get(reverse('metodos_pagos'))
        self.assertEqual(response.status_code, 302)  # Redirección
    
    def test_acceso_usuario_normal(self):
        """Test que usuario normal no puede acceder"""
        self.client.login(username='user', password='testpass123')
        response = self.client.get(reverse('metodos_pagos'))
        self.assertEqual(response.status_code, 302)  # Redirección a home
    
    def test_acceso_superusuario(self):
        """Test que superusuario puede acceder"""
        self.client.login(username='admin', password='testpass123')
        response = self.client.get(reverse('metodos_pagos'))
        self.assertEqual(response.status_code, 200)
    
    def test_lista_metodos_pago(self):
        """Test vista de lista"""
        self.client.login(username='admin', password='testpass123')
        response = self.client.get(reverse('metodos_pagos'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Tarjeta de Crédito")
        self.assertIn('metodos_pagos', response.context)
        self.assertIn('form', response.context)
    
    def test_crear_metodo_pago_get(self):
        """Test GET para crear método de pago"""
        self.client.login(username='admin', password='testpass123')
        response = self.client.get(reverse('metodos-pagos-agregar'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Agregar Método de Pago")
    
    def test_crear_metodo_pago_post_valido(self):
        """Test POST válido para crear método de pago"""
        self.client.login(username='admin', password='testpass123')
        data = {
            'nombre': 'PayPal',
            'descripcion': 'Pagos en línea'
        }
        response = self.client.post(reverse('metodos-pagos-agregar'), data)
        self.assertEqual(response.status_code, 302)  # Redirección tras éxito
        self.assertTrue(MetodoPago.objects.filter(nombre='PayPal').exists())
    
    def test_crear_metodo_pago_post_invalido(self):
        """Test POST inválido para crear método de pago"""
        self.client.login(username='admin', password='testpass123')
        data = {'nombre': ''}  # Nombre vacío
        response = self.client.post(reverse('metodos-pagos-agregar'), data)
        self.assertEqual(response.status_code, 200)  # Vuelve al formulario
        self.assertContains(response, 'obligatorio')
    
    def test_editar_metodo_pago_get(self):
        """Test GET para editar método de pago"""
        self.client.login(username='admin', password='testpass123')
        url = reverse('metodos-pagos-editar', kwargs={'pk': self.metodo_pago.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Editar Método de pago")
        self.assertContains(response, "Tarjeta de Crédito")
    
    def test_editar_metodo_pago_post_valido(self):
        """Test POST válido para editar método de pago"""
        self.client.login(username='admin', password='testpass123')
        url = reverse('metodos-pagos-editar', kwargs={'pk': self.metodo_pago.pk})
        data = {
            'nombre': 'Tarjeta de Débito',
            'descripcion': 'Pagos con débito'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        
        # Verificar que se actualizó
        self.metodo_pago.refresh_from_db()
        self.assertEqual(self.metodo_pago.nombre, 'Tarjeta de Débito')
    
    def test_detalle_metodo_pago_ajax(self):
        """Test vista AJAX de detalle"""
        self.client.login(username='admin', password='testpass123')
        url = reverse('metodos-pagos-detalle', kwargs={'pk': self.metodo_pago.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertEqual(data['nombre'], 'Tarjeta de Crédito')
        self.assertEqual(data['descripcion'], 'Pagos con tarjeta')
    
    def test_activar_metodo_pago(self):
        """Test activar método de pago"""
        self.client.login(username='admin', password='testpass123')
        url = reverse('metodos-pagos-activate', kwargs={'pk': self.metodo_pago.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        
        self.metodo_pago.refresh_from_db()
        self.assertTrue(self.metodo_pago.activo)
    
    def test_desactivar_metodo_pago(self):
        """Test desactivar método de pago"""
        # Primero activarlo
        self.metodo_pago.activo = True
        self.metodo_pago.save()
        
        self.client.login(username='admin', password='testpass123')
        url = reverse('metodos-pagos-desactivate', kwargs={'pk': self.metodo_pago.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        
        self.metodo_pago.refresh_from_db()
        self.assertFalse(self.metodo_pago.activo)


class MetodoPagoAjaxValidationTests(TestCase):
    """Tests para la validación AJAX de nombres"""
    
    def setUp(self):
        """Configuración inicial"""
        self.client = Client()
        self.superuser = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='testpass123'
        )
        self.metodo_existente = MetodoPago.objects.create(
            nombre="Tarjeta de Crédito"
        )
    
    def test_validar_nombre_nuevo_valido(self):
        """Test validación AJAX - nombre nuevo válido"""
        self.client.login(username='admin', password='testpass123')
        response = self.client.post(reverse('metodos-pagos-validar-nombre'), {
            'nombre': 'PayPal',
            'current_id': ''
        })
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertTrue(data['valid'])
    
    def test_validar_nombre_duplicado(self):
        """Test validación AJAX - nombre duplicado"""
        self.client.login(username='admin', password='testpass123')
        response = self.client.post(reverse('metodos-pagos-validar-nombre'), {
            'nombre': 'Tarjeta de Crédito',
            'current_id': ''
        })
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertFalse(data['valid'])
        self.assertIn('ya existe', data['message'])
    
    def test_validar_nombre_duplicado_case_insensitive(self):
        """Test validación AJAX - duplicado case insensitive"""
        self.client.login(username='admin', password='testpass123')
        response = self.client.post(reverse('metodos-pagos-validar-nombre'), {
            'nombre': 'TARJETA DE CRÉDITO',
            'current_id': ''
        })
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertFalse(data['valid'])
    
    def test_validar_edicion_mismo_nombre(self):
        """Test validación AJAX - edición con mismo nombre"""
        self.client.login(username='admin', password='testpass123')
        response = self.client.post(reverse('metodos-pagos-validar-nombre'), {
            'nombre': 'Tarjeta de Crédito',
            'current_id': str(self.metodo_existente.pk)
        })
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertTrue(data['valid'])  # Debe ser válido porque es el mismo registro
    
    def test_validar_nombre_vacio(self):
        """Test validación AJAX - nombre vacío"""
        self.client.login(username='admin', password='testpass123')
        response = self.client.post(reverse('metodos-pagos-validar-nombre'), {
            'nombre': '',
            'current_id': ''
        })
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertFalse(data['valid'])
    
    def test_acceso_no_autenticado_ajax(self):
        """Test que la validación AJAX requiere autenticación"""
        response = self.client.post(reverse('metodos-pagos-validar-nombre'), {
            'nombre': 'PayPal',
            'current_id': ''
        })
        self.assertEqual(response.status_code, 302)  # Redirección a login


class MetodoPagoIntegrationTests(TestCase):
    """Tests de integración completos"""
    
    def setUp(self):
        self.client = Client()
        self.superuser = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='testpass123'
        )
        self.client.login(username='admin', password='testpass123')
    
    def test_flujo_completo_crear_editar_eliminar(self):
        """Test del flujo completo de CRUD"""
        # 1. Crear
        response = self.client.post(reverse('metodos-pagos-agregar'), {
            'nombre': 'Bitcoin',
            'descripcion': 'Criptomoneda'
        })
        self.assertEqual(response.status_code, 302)
        
        metodo = MetodoPago.objects.get(nombre='Bitcoin')
        self.assertFalse(metodo.activo)  # Por defecto False
        
        # 2. Editar
        response = self.client.post(reverse('metodos-pagos-editar', kwargs={'pk': metodo.pk}), {
            'nombre': 'Bitcoin Cash',
            'descripcion': 'Criptomoneda mejorada'
        })
        self.assertEqual(response.status_code, 302)
        
        metodo.refresh_from_db()
        self.assertEqual(metodo.nombre, 'Bitcoin Cash')
        
        # 3. Activar
        response = self.client.post(reverse('metodos-pagos-activate', kwargs={'pk': metodo.pk}))
        metodo.refresh_from_db()
        self.assertTrue(metodo.activo)
        
        # 4. Desactivar  
        response = self.client.post(reverse('metodos-pagos-desactivate', kwargs={'pk': metodo.pk}))
        metodo.refresh_from_db()
        self.assertFalse(metodo.activo)
    
    def test_prevenir_nombres_duplicados_completo(self):
        """Test completo de prevención de duplicados"""
        # Crear primero
        self.client.post(reverse('metodos-pagos-agregar'), {
            'nombre': 'PayPal',
            'descripcion': 'Original'
        })
        
        # Intentar crear duplicado
        response = self.client.post(reverse('metodos-pagos-agregar'), {
            'nombre': 'PayPal',
            'descripcion': 'Duplicado'
        })
        self.assertEqual(response.status_code, 200)  # Vuelve al formulario con error
        self.assertContains(response, 'ya existe')
        
        # Verificar que solo existe uno
        self.assertEqual(MetodoPago.objects.filter(nombre='PayPal').count(), 1)
    
    def test_paginacion(self):
        """Test de paginación en la lista"""
        # Crear más de 8 métodos (paginate_by = 8)
        for i in range(10):
            MetodoPago.objects.create(nombre=f'Método {i:02d}')
        
        response = self.client.get(reverse('metodos_pagos'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['is_paginated'])
        self.assertEqual(len(response.context['metodos_pagos']), 8)


# Tests de rendimiento (opcional)
class MetodoPagoPerformanceTests(TestCase):
    """Tests de rendimiento básicos"""
    
    def setUp(self):
        self.client = Client()
        self.superuser = User.objects.create_superuser(
            username='admin',
            email='admin@test.com', 
            password='testpass123'
        )
        self.client.login(username='admin', password='testpass123')
        
        # Crear muchos registros para probar rendimiento
        for i in range(100):
            MetodoPago.objects.create(nombre=f'Método {i:03d}')
    
    def test_lista_con_muchos_registros(self):
        """Test que la lista funciona con muchos registros"""
        response = self.client.get(reverse('metodos_pagos'))
        self.assertEqual(response.status_code, 200)
        # Verificar que se ejecuta en tiempo razonable
        self.assertLess(len(response.content), 50000)  # Respuesta no demasiado grande