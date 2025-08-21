from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.db.models.functions import TruncMonth
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.http import HttpResponse, JsonResponse
from django.urls import reverse_lazy
from django.views.decorators.csrf import csrf_exempt
import json
from .models import Cliente, Segmentacion

def clientes(request):
    return render(request, 'clientes/lista.html')

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

class ClienteCreateView(CreateView):
    model = Cliente
    template_name = 'clientes/form.html'
    fields = ['nombre', 'email', 'telefono', 'segmentacion', 'estado']
    success_url = reverse_lazy('clientes')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["segmentaciones"] = Segmentacion.objects.all()
        return context
    
    def get_queryset(self):
        return Cliente.objects.all().order_by('-id')

class ClienteUpdateView(UpdateView):
    model = Cliente
    template_name = 'clientes/form.html'
    fields = ['nombre', 'email', 'telefono', 'segmentacion', 'estado']
    success_url = reverse_lazy('clientes')
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["segmentaciones"] = Segmentacion.objects.all()
        return context

class ClienteDeleteView(DeleteView):
    model = Cliente
    template_name = 'clientes/form.html'
    success_url = reverse_lazy('clientes')
    def delete(self, request, *args, **kwargs):
        messages.success(request, "Cliente eliminado correctamente.")
        return super().delete(request, *args, **kwargs)