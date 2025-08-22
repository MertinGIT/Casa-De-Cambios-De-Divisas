# views.py
from functools import wraps
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import ListView, CreateView, UpdateView, DeleteView

from .models import Cliente, Segmentacion



def superadmin_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated:
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            else:
                # Usuario normal no tiene acceso
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
        return context


@method_decorator(superadmin_required, name='dispatch')
class ClienteCreateView(CreateView):
    model = Cliente
    template_name = 'clientes/form.html'
    fields = ['nombre', 'email', 'telefono', 'segmentacion', 'estado']
    success_url = reverse_lazy('clientes')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["segmentaciones"] = Segmentacion.objects.all()
        return context


@method_decorator(superadmin_required, name='dispatch')
class ClienteUpdateView(UpdateView):
    model = Cliente
    template_name = 'clientes/form.html'
    fields = ['nombre', 'email', 'telefono', 'segmentacion', 'estado']
    success_url = reverse_lazy('clientes')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["segmentaciones"] = Segmentacion.objects.all()
        return context


@method_decorator(superadmin_required, name='dispatch')
class ClienteDeleteView(DeleteView):
    model = Cliente
    template_name = 'clientes/form.html'
    success_url = reverse_lazy('clientes')

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Cliente eliminado correctamente.")
        return super().delete(request, *args, **kwargs)
