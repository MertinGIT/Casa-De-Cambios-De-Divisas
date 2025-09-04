# views.py - Solución mejorada
from functools import wraps
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json
from .models import MetodoPago
from .forms import MetodoPagoForm
from django.template.loader import render_to_string
import logging

logger = logging.getLogger(__name__)

def superadmin_required(view_func):
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
    return render(request, 'metodos_pagos/lista.html')

@method_decorator(superadmin_required, name='dispatch')
class MetodoPagoListView(ListView):
    model = MetodoPago
    template_name = 'metodos_pagos/lista.html'
    context_object_name = 'metodos_pagos'
    paginate_by = 8

    def get_queryset(self):
        return MetodoPago.objects.all().order_by('-id')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = MetodoPagoForm()
        context["form_action"] = reverse_lazy('metodos-pagos-agregar')
        return context

@method_decorator(superadmin_required, name='dispatch')
class MetodoPagoCreateView(CreateView):
    model = MetodoPago
    form_class = MetodoPagoForm
    template_name = 'metodos_pagos/lista.html'
    success_url = reverse_lazy('metodos_pagos')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["metodos_pagos"] = MetodoPago.objects.all().order_by('-id')
        context["modal_title"] = "Agregar Método de Pago"
        context["form_action"] = reverse_lazy('metodos-pagos-agregar')
        return context

    def form_valid(self, form):
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
    model = MetodoPago
    form_class = MetodoPagoForm
    template_name = 'metodos_pagos/lista.html'
    success_url = reverse_lazy('metodos_pagos')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["metodos_pagos"] = MetodoPago.objects.all().order_by('-id')
        context["modal_title"] = "Editar Método de pago"
        context["form_action"] = reverse_lazy('metodos-pagos-editar', kwargs={'pk': self.object.pk})
        return context

    def form_valid(self, form):
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
    model = MetodoPago
    template_name = 'metodos_pagos/form.html'
    success_url = reverse_lazy('metodos_pagos')
    fields = []  # No necesitamos formulario, solo acción de desactivar

    def post(self, request, *args, **kwargs):
        metodo_pago = self.get_object()
        metodo_pago.activo = False
        metodo_pago.save()
        messages.success(request, "Método de pago desactivado correctamente.")
        return redirect(self.success_url)
    
@method_decorator(superadmin_required, name='dispatch')
class MetodoPagoActivateView(UpdateView):
    model = MetodoPago
    template_name = 'metodos_pagos/form.html'
    success_url = reverse_lazy('metodos_pagos')
    fields = [] 

    def post(self, request, *args, **kwargs):
        metodo_pago = self.get_object()
        metodo_pago.activo = True
        metodo_pago.save()
        messages.success(request, "Método de pago activado correctamente.")
        return redirect(self.success_url)

def MetodoPago_detalle(request, pk):
    metodo_pago = get_object_or_404(MetodoPago, pk=pk)
    return JsonResponse({
        "nombre": metodo_pago.nombre,
        "descripcion": metodo_pago.descripcion,
        "activo": metodo_pago.activo,
    })

@require_POST
@superadmin_required
def validar_nombre_metodo_pago(request):
    """Vista AJAX para validar unicidad del nombre en tiempo real"""
    try:
        nombre = request.POST.get('nombre', '').strip()
        current_id = request.POST.get('current_id', '').strip()
        
        if not nombre:
            return JsonResponse({'valid': False, 'message': 'Nombre requerido'})
        
        # Normalizar texto como en el formulario
        import unicodedata
        nombre_normalizado = unicodedata.normalize('NFKC', nombre).strip()
        
        # Verificar unicidad
        qs = MetodoPago.objects.filter(nombre__iexact=nombre_normalizado)
        
        # Excluir el registro actual si estamos editando
        if current_id and current_id.isdigit():
            qs = qs.exclude(pk=int(current_id))
        
        exists = qs.exists()
        
        return JsonResponse({
            'valid': not exists,
            'message': 'El método de pago ya existe.' if exists else 'Disponible'
        })
        
    except Exception as e:
        logger.error(f"Error validando nombre: {e}")
        return JsonResponse({'valid': False, 'message': 'Error de validación'})