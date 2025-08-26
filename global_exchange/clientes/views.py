# views.py - Solución simple
from functools import wraps
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.http import JsonResponse
from .models import Cliente, Segmentacion
from .forms import ClienteForm
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
def clientes(request):
    return render(request, 'clientes/lista.html')

@method_decorator(superadmin_required, name='dispatch')
class ClienteListView(ListView):
    model = Cliente
    template_name = 'clientes/lista.html'
    context_object_name = 'clientes'
    paginate_by = 8

    def get_queryset(self):
        return Cliente.objects.all().order_by('-id')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["segmentaciones"] = Segmentacion.objects.all()
        context["form"] = ClienteForm()
        context["form_action"] = reverse_lazy('clientes-agregar')
        return context

@method_decorator(superadmin_required, name='dispatch')
class ClienteCreateView(CreateView):
    model = Cliente
    form_class = ClienteForm
    template_name = 'clientes/lista.html'
    success_url = reverse_lazy('clientes')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["clientes"] = Cliente.objects.all().order_by('-id')
        context["segmentaciones"] = Segmentacion.objects.all()
        context["modal_title"] = "Agregar Cliente"
        context["form_action"] = reverse_lazy('clientes-agregar')
        return context

    def form_valid(self, form):
        form.instance.estado = 'activo'
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            try:
                self.object = form.save()
                logger.info(f"Cliente guardado exitosamente: {self.object.id}")
                return JsonResponse({'success': True})
            except Exception as e:
                logger.error(f"Error guardando cliente: {str(e)}")
                return JsonResponse({'success': False, 'error': 'Error interno del servidor'})
        return super().form_valid(form)

    def form_invalid(self, form):
        logger.error(f"Formulario inválido. Errores: {form.errors}")
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            # Generar HTML manualmente con los errores
            html_form = self.generate_form_html_with_errors(form)
            return JsonResponse({
                'success': False, 
                'html_form': html_form
            })
        return super().form_invalid(form)
    
    def generate_form_html_with_errors(self, form):
        """Genera el HTML del formulario con errores manualmente"""
        html = '<div id="form-fields-container">'
        
        # Campo nombre
        nombre_errors = form.errors.get('nombre', [])
        html += f'''
        <div class="form-group">
            <label for="id_nombre">Nombre</label>
            <div class="input-icon">
                <span class="icon">👤</span>
                <input type="text" name="nombre" value="{form.data.get('nombre', '')}" 
                       class="custom-input{' error' if nombre_errors else ''}" 
                       placeholder="Ingrese el nombre" id="id_nombre">
            </div>
            {f'<div class="error-messages">{"".join([f"<span class=\"error-text\">{error}</span>" for error in nombre_errors])}</div>' if nombre_errors else ''}
        </div>
        '''
        
        # Campo email
        email_errors = form.errors.get('email', [])
        html += f'''
        <div class="form-group">
            <label for="id_email">Email</label>
            <div class="input-icon">
                <span class="icon">📧</span>
                <input type="email" name="email" value="{form.data.get('email', '')}" 
                       class="custom-input{' error' if email_errors else ''}" 
                       placeholder="Ingrese el correo" id="id_email">
            </div>
            {f'<div class="error-messages">{"".join([f"<span class=\"error-text\">{error}</span>" for error in email_errors])}</div>' if email_errors else ''}
        </div>
        '''
        
        # Campo telefono
        telefono_errors = form.errors.get('telefono', [])
        html += f'''
        <div class="form-group">
            <label for="id_telefono">Teléfono</label>
            <div class="input-icon">
                <span class="icon">📞</span>
                <input type="text" name="telefono" value="{form.data.get('telefono', '')}" 
                       class="custom-input{' error' if telefono_errors else ''}" 
                       placeholder="Ingrese teléfono" id="id_telefono">
            </div>
            {f'<div class="error-messages">{"".join([f"<span class=\"error-text\">{error}</span>" for error in telefono_errors])}</div>' if telefono_errors else ''}
        </div>
        '''
        
        # Campo segmentacion
        segmentacion_errors = form.errors.get('segmentacion', [])
        selected_segmentacion = form.data.get('segmentacion', '')
        segmentaciones_options = ''
        segmentaciones_options += '<option value="">Seleccione un segmento</option>'
        for seg in Segmentacion.objects.all():
            selected = 'selected' if str(seg.id) == str(selected_segmentacion) else ''
            segmentaciones_options += f'<option value="{seg.id}" {selected}>{seg.nombre}</option>'
            
        html += f'''
        <div class="form-group">
            <label for="id_segmentacion">Segmentación</label>
            <div class="input-icon">
                <span class="icon">🏷️</span>
                <select name="segmentacion" class="custom-input{' error' if segmentacion_errors else ''}" id="id_segmentacion">
                    {segmentaciones_options}
                </select>
            </div>
            {f'<div class="error-messages">{"".join([f"<span class=\"error-text\">{error}</span>" for error in segmentacion_errors])}</div>' if segmentacion_errors else ''}
        </div>
        '''
        
        # Campo estado
        estado_errors = form.errors.get('estado', [])
        html += f'''
        <div class="form-group">
            <label for="id_estado">Estado</label>
            <div class="input-icon">
                <span class="icon">⚡</span>
                <input type="text" name="estado" value="{form.data.get('estado', 'activo')}" 
                       class="custom-input{' error' if estado_errors else ''}" 
                       readonly id="id_estado">
            </div>
            {f'<div class="error-messages">{"".join([f"<span class=\"error-text\">{error}</span>" for error in estado_errors])}</div>' if estado_errors else ''}
        </div>
        '''
        
        html += '</div>'
        return html

@method_decorator(superadmin_required, name='dispatch')
class ClienteUpdateView(UpdateView):
    model = Cliente
    form_class = ClienteForm
    template_name = 'clientes/lista.html'
    success_url = reverse_lazy('clientes')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["segmentaciones"] = Segmentacion.objects.all()
        context["modal_title"] = "Editar Cliente"
        context["form_action"] = reverse_lazy('clientes-editar', kwargs={'pk': self.object.pk})
        return context

    def form_valid(self, form):
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            try:
                self.object = form.save()
                return JsonResponse({'success': True})
            except Exception as e:
                return JsonResponse({'success': False, 'error': 'Error interno del servidor'})
        return super().form_valid(form)

    def form_invalid(self, form):
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            # Usar el mismo método para generar HTML con errores
            create_view = ClienteCreateView()
            html_form = create_view.generate_form_html_with_errors(form)
            return JsonResponse({'success': False, 'html_form': html_form})
        return super().form_invalid(form)

@method_decorator(superadmin_required, name='dispatch')
class ClienteDeleteView(DeleteView):
    model = Cliente
    template_name = 'clientes/form.html'
    success_url = reverse_lazy('clientes')

    def delete(self, request, *args, **kwargs):
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            try:
                cliente = self.get_object()
                cliente_nombre = cliente.nombre
                cliente.delete()
                return JsonResponse({'success': True})
            except Exception as e:
                return JsonResponse({'success': False, 'error': 'Error interno del servidor'})
        
        messages.success(request, "Cliente eliminado correctamente.")
        return super().delete(request, *args, **kwargs)

def cliente_detalle(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    return JsonResponse({
        "nombre": cliente.nombre,
        "email": cliente.email,
        "telefono": cliente.telefono,
        "segmentacion": cliente.segmentacion.id if cliente.segmentacion else None,
        "estado": cliente.estado,
    })