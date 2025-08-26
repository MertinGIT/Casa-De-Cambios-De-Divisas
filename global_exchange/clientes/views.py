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
    def form_invalid(self, form):
        logger.error("❌ Errores en formulario: %s", form.errors)
        messages.error(self.request, f"Errores en el formulario: {form.errors}")
        return super().form_invalid(form)

    def form_valid(self, form):
        logger.info("✅ Formulario válido, guardando cliente")
        messages.success(self.request, "Cliente agregado correctamente.")
        return super().form_valid(form)


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