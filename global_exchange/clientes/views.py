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
    

@superadmin_required
def check_email(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        obj_id = request.POST.get('obj_id')
        
        # Debug: imprimir valores recibidos
        print(f"Email: {email}, obj_id: {obj_id}")
        
        query = Cliente.objects.filter(email=email)
        
        # Si hay obj_id, excluir ese registro de la validación
        if obj_id and obj_id != 'null' and obj_id != '':
            query = query.exclude(id=obj_id)
        
        exists = query.exists()
        
        return JsonResponse(not exists, safe=False)         

  
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
        messages.success(request, "Cliente eliminado correctamente.")
        return super().delete(request, *args, **kwargs)
        


@method_decorator(superadmin_required, name='dispatch')
class ClienteDesactivateView(UpdateView):
    model = Cliente
    template_name = 'clientes/form.html'
    success_url = reverse_lazy('clientes')
    fields = []  # No necesitamos formulario, solo acción de desactivar

    def post(self, request, *args, **kwargs):
        cliente = self.get_object()
        cliente.estado = 'inactivo'
        cliente.save()
        messages.success(request, "Cliente desactivado correctamente.")
        return redirect(self.success_url)
    
@method_decorator(superadmin_required, name='dispatch')
class ClienteActivateView(UpdateView):
    model = Cliente
    template_name = 'clientes/form.html'
    success_url = reverse_lazy('clientes')
    fields = [] 

    def post(self, request, *args, **kwargs):
        cliente = self.get_object()
        cliente.estado = 'activo'
        cliente.save()
        messages.success(request, "Cliente activo correctamente.")
        return redirect(self.success_url)

        

def cliente_detalle(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    return JsonResponse({
        "nombre": cliente.nombre,
        "email": cliente.email,
        "telefono": cliente.telefono,
        "segmentacion": cliente.segmentacion.id if cliente.segmentacion else None,
        "estado": cliente.estado,
    })