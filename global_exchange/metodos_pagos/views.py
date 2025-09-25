"""
VISTAS PARA GESTIÓN DE MÉTODOS DE PAGO
=====================================

Este módulo contiene todas las vistas para el CRUD completo de métodos de pago
con funcionalidades avanzadas de búsqueda, filtrado y validación.

Funcionalidades principales:
- Lista paginada con búsqueda avanzada
- Creación y edición de métodos de pago
- Activación/desactivación de registros
- Validación AJAX en tiempo real
- Control de acceso por roles (superadmin)

Arquitectura:
- Vistas basadas en clases (CBV) para operaciones CRUD
- Decoradores personalizados para autenticación
- Manejo centralizado de errores y logging
- Búsqueda con Django Q objects
"""

from functools import wraps
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.db.models import Q
import json
from .models import MetodoPago
from .forms import MetodoPagoForm
from django.template.loader import render_to_string
import logging

logger = logging.getLogger(__name__)

def superadmin_required(view_func):
    """
    Decorador personalizado para restringir acceso solo a superusuarios.
    
    Funcionalidad:
    - Verifica que el usuario esté autenticado
    - Valida que tenga permisos de superadmin
    - Redirige a login si no está autenticado
    - Redirige a home si no tiene permisos
    
    Args:
        view_func: Función de vista a proteger
        
    Returns:
        Función decorada con validación de permisos
        
    Uso:
        @superadmin_required
        def mi_vista(request):
            pass
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated:
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            else:
                return redirect('home')
        return redirect('login')
    return _wrapped_view

@superadmin_required
def metodos_pagos(request):
    """
    Vista funcional simple para renderizar la lista de métodos de pago.
    
    Esta vista está siendo deprecada en favor de MetodoPagoListView
    que ofrece más funcionalidades.
    
    Args:
        request: HttpRequest object
        
    Returns:
        HttpResponse con template renderizado
    """
    return render(request, 'metodos_pagos/lista.html')

@method_decorator(superadmin_required, name='dispatch')
class MetodoPagoListView(ListView):
    """
    Vista principal para listar métodos de pago con búsqueda avanzada.
    
    Características:
    - Paginación automática (8 elementos por página)
    - Búsqueda por nombre y/o descripción
    - Filtrado específico por campo
    - Ordenamiento por ID descendente
    - Mantenimiento de estado de búsqueda
    
    Parámetros GET soportados:
    - q: Término de búsqueda
    - campo: Campo específico donde buscar ('nombre', 'descripcion')
    - page: Número de página para paginación
    
    Context variables:
    - metodos_pagos: QuerySet paginado de métodos de pago
    - form: Formulario vacío para modal de creación
    - form_action: URL para envío del formulario
    - q: Término de búsqueda actual
    - campo_selected: Campo de búsqueda seleccionado
    """
    model = MetodoPago
    template_name = 'metodos_pagos/lista.html'
    context_object_name = 'metodos_pagos'
    paginate_by = 8

    def get_queryset(self):
        """
        Construye el QuerySet con filtros de búsqueda aplicados.
        
        Lógica de búsqueda:
        1. Si se especifica 'campo' y 'q': busca solo en ese campo
        2. Si solo se especifica 'q': busca en nombre y descripción
        3. Sin parámetros: devuelve todos los registros
        
        Returns:
            QuerySet filtrado y ordenado de MetodoPago
        """
        # Obtener y limpiar parámetros de búsqueda
        q = self.request.GET.get('q', '').strip()
        campo = self.request.GET.get('campo', '').strip()
        
        # QuerySet base ordenado por ID descendente (más recientes primero)
        queryset = MetodoPago.objects.all().order_by('-id')
        
        # Aplicar filtros de búsqueda si existe término de búsqueda
        if q:
            if campo == 'nombre':
                # Búsqueda específica por nombre (case-insensitive)
                queryset = queryset.filter(nombre__icontains=q)
            elif campo == 'descripcion':
                # Búsqueda específica por descripción (case-insensitive)
                queryset = queryset.filter(descripcion__icontains=q)
            else:
                # Búsqueda general en ambos campos usando Q objects
                queryset = queryset.filter(
                    Q(nombre__icontains=q) | Q(descripcion__icontains=q)
                )
        
        return queryset

    def get_context_data(self, **kwargs):
        """
        Agrega contexto adicional para el template.
        
        Variables agregadas:
        - form: Formulario vacío para modal de creación
        - form_action: URL para POST del formulario
        - q: Término de búsqueda para mantener en input
        - campo_selected: Campo de búsqueda seleccionado
        
        Returns:
            Dict con contexto extendido
        """
        context = super().get_context_data(**kwargs)
        
        # Formulario para modal de creación
        context["form"] = MetodoPagoForm()
        context["form_action"] = reverse_lazy('metodos-pagos-agregar')
        
        # Mantener estado de búsqueda en el template
        context["q"] = self.request.GET.get('q', '')
        context["campo_selected"] = self.request.GET.get('campo', '')
        
        return context

@method_decorator(superadmin_required, name='dispatch')
class MetodoPagoCreateView(CreateView):
    """
    Vista para crear nuevos métodos de pago.
    
    Funcionalidades:
    - Validación automática del formulario
    - Mensajes de éxito/error
    - Logging de errores
    - Redirección a lista después de crear
    
    En caso de error:
    - Log del error para debugging
    - Mensaje de error para el usuario
    - Regresa al formulario con errores mostrados
    """
    model = MetodoPago
    form_class = MetodoPagoForm
    template_name = 'metodos_pagos/lista.html'
    success_url = reverse_lazy('metodos_pagos')

    def get_context_data(self, **kwargs):
        """
        Contexto para modal de creación.
        
        Incluye:
        - Lista completa de métodos de pago
        - Título del modal
        - URL de acción del formulario
        """
        context = super().get_context_data(**kwargs)
        context["metodos_pagos"] = MetodoPago.objects.all().order_by('-id')
        context["modal_title"] = "Agregar Método de Pago"
        context["form_action"] = reverse_lazy('metodos-pagos-agregar')
        return context

    def form_valid(self, form):
        """
        Procesa formulario válido con manejo de errores.
        
        Args:
            form: Formulario validado
            
        Returns:
            HttpResponse de éxito o error
        """
        try:
            response = super().form_valid(form)
            messages.success(self.request, "Método de pago agregado correctamente.")
            return response
        except Exception as e:
            logger.error(f"Error creando método de pago: {e}")
            messages.error(self.request, "Error al agregar el método de pago.")
            return self.form_invalid(form)

@method_decorator(superadmin_required, name='dispatch')
class MetodoPagoUpdateView(UpdateView):
    """
    Vista para editar métodos de pago existentes.
    
    Características:
    - Carga automática del objeto a editar
    - Validación con manejo de errores
    - Mensajes informativos al usuario
    - Logging para debugging
    """
    model = MetodoPago
    form_class = MetodoPagoForm
    template_name = 'metodos_pagos/lista.html'
    success_url = reverse_lazy('metodos_pagos')

    def get_context_data(self, **kwargs):
        """
        Contexto para modal de edición.
        
        Incluye:
        - Lista actualizada de métodos de pago
        - Título específico para edición
        - URL con PK del objeto a editar
        """
        context = super().get_context_data(**kwargs)
        context["metodos_pagos"] = MetodoPago.objects.all().order_by('-id')
        context["modal_title"] = "Editar Método de pago"
        context["form_action"] = reverse_lazy('metodos-pagos-editar', kwargs={'pk': self.object.pk})
        return context

    def form_valid(self, form):
        """
        Procesa actualización con manejo de errores.
        
        Args:
            form: Formulario validado con cambios
            
        Returns:
            HttpResponse de éxito o error
        """
        try:
            response = super().form_valid(form)
            messages.success(self.request, "Método de pago actualizado correctamente.")
            return response
        except Exception as e:
            logger.error(f"Error actualizando método de pago: {e}")
            messages.error(self.request, "Error al actualizar el método de pago.")
            return self.form_invalid(form)

@method_decorator(superadmin_required, name='dispatch')
class MetodoPagoDesactivateView(UpdateView):
    """
    Vista para desactivar métodos de pago.
    
    Funcionalidad:
    - Cambia el campo 'activo' a False
    - No elimina el registro (soft delete)
    - Solo acepta método POST
    - Mensaje de confirmación al usuario
    
    Uso típico:
    - Deshabilitar métodos de pago obsoletos
    - Mantener histórico de transacciones
    - Evitar eliminación accidental de datos
    """
    model = MetodoPago
    template_name = 'metodos_pagos/form.html'
    success_url = reverse_lazy('metodos_pagos')
    fields = []  # No necesitamos formulario, solo acción de desactivar

    def post(self, request, *args, **kwargs):
        """
        Procesa desactivación del método de pago.
        
        Args:
            request: HttpRequest con datos POST
            *args, **kwargs: Argumentos de URL (incluye pk)
            
        Returns:
            HttpResponseRedirect a lista con mensaje de éxito
        """
        metodo_pago = self.get_object()
        metodo_pago.activo = False
        metodo_pago.save()
        messages.success(request, "Método de pago desactivado correctamente.")
        return redirect(self.success_url)
    
@method_decorator(superadmin_required, name='dispatch')
class MetodoPagoActivateView(UpdateView):
    """
    Vista para reactivar métodos de pago desactivados.
    
    Funcionalidad:
    - Cambia el campo 'activo' a True
    - Restaura disponibilidad del método de pago
    - Solo acepta método POST
    - Mensaje de confirmación al usuario
    
    Casos de uso:
    - Rehabilitar métodos de pago temporalmente suspendidos
    - Corregir desactivaciones accidentales
    - Gestión dinámica de métodos disponibles
    """
    model = MetodoPago
    template_name = 'metodos_pagos/form.html'
    success_url = reverse_lazy('metodos_pagos')
    fields = [] 

    def post(self, request, *args, **kwargs):
        """
        Procesa activación del método de pago.
        
        Args:
            request: HttpRequest con datos POST
            *args, **kwargs: Argumentos de URL (incluye pk)
            
        Returns:
            HttpResponseRedirect a lista con mensaje de éxito
        """
        metodo_pago = self.get_object()
        metodo_pago.activo = True
        metodo_pago.save()
        messages.success(request, "Método de pago activado correctamente.")
        return redirect(self.success_url)

def MetodoPago_detalle(request, pk):
    """
    Vista AJAX para obtener detalles de un método de pago.
    
    Uso típico:
    - Cargar datos en modals de edición
    - Mostrar información sin recargar página
    - APIs internas para frontend
    
    Args:
        request: HttpRequest
        pk: Primary key del método de pago
        
    Returns:
        JsonResponse con datos del método de pago
        
    Response format:
        {
            "nombre": "string",
            "descripcion": "string", 
            "activo": boolean
        }
        
    Excepciones:
        Http404: Si no existe el método de pago con ese pk
    """
    metodo_pago = get_object_or_404(MetodoPago, pk=pk)
    return JsonResponse({
        "nombre": metodo_pago.nombre,
        "descripcion": metodo_pago.descripcion,
        "activo": metodo_pago.activo,
    })

@require_POST
@superadmin_required
def validar_nombre_metodo_pago(request):
    """
    Vista AJAX para validar unicidad del nombre en tiempo real.
    
    Funcionalidades:
    - Validación mientras el usuario escribe
    - Normalización de texto Unicode
    - Exclusión del registro actual en edición
    - Verificación case-insensitive
    
    Parámetros POST:
    - nombre: Nombre a validar (requerido)
    - current_id: ID del registro actual en edición (opcional)
    
    Returns:
        JsonResponse con resultado de validación
        
    Response format:
        {
            "valid": boolean,
            "message": "string"
        }
        
    Casos de uso:
    - Evitar duplicados antes de enviar formulario
    - Feedback inmediato al usuario
    - Mejorar UX en formularios
        
    Excepciones manejadas:
    - Errores de validación general
    - Problemas de normalización de texto
    - Errores de consulta a base de datos
    """
    try:
        # Obtener y limpiar parámetros
        nombre = request.POST.get('nombre', '').strip()
        current_id = request.POST.get('current_id', '').strip()
        
        # Validación básica
        if not nombre:
            return JsonResponse({'valid': False, 'message': 'Nombre requerido'})
        
        # Normalizar texto para comparación consistente
        import unicodedata
        nombre_normalizado = unicodedata.normalize('NFKC', nombre).strip()
        
        # Construir query para verificar unicidad
        qs = MetodoPago.objects.filter(nombre__iexact=nombre_normalizado)
        
        # Excluir el registro actual si estamos editando
        if current_id and current_id.isdigit():
            qs = qs.exclude(pk=int(current_id))
        
        # Verificar si existe
        exists = qs.exists()
        
        return JsonResponse({
            'valid': not exists,
            'message': 'El método de pago ya existe.' if exists else 'Disponible'
        })
        
    except Exception as e:
        # Log del error para debugging
        logger.error(f"Error validando nombre: {e}")
        return JsonResponse({'valid': False, 'message': 'Error de validación'})