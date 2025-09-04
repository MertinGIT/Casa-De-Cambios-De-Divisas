from functools import wraps
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.http import JsonResponse
from .models import Cliente, Segmentacion
from .forms import ClienteForm
import logging

logger = logging.getLogger(__name__)

def superadmin_required(view_func):
    """
    Decorador que restringe el acceso a usuarios superadministradores.

    Si el usuario no está autenticado, redirige a 'login'.
    Si está autenticado pero no es superusuario, redirige a 'home'.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated:
            if request.user.is_superuser or request.user.groups.filter(name='ADMIN').exists():
                return view_func(request, *args, **kwargs)
            return redirect('home')
        return redirect('login')
    return _wrapped_view

@superadmin_required
def clientes(request):
    """
    Renderiza la vista principal de clientes.
    """
    return render(request, 'clientes/lista.html')


@method_decorator(superadmin_required, name='dispatch')
class ClienteListView(ListView):
    """
    Vista basada en clases para listar clientes con paginación.
    Filtra solo por nombre y segmento si se recibe q y campo.
    """
    model = Cliente
    template_name = 'clientes/lista.html'
    context_object_name = 'clientes'
    paginate_by = 8

    def get_queryset(self):
        queryset = Cliente.objects.all().order_by('-id')
        q = self.request.GET.get("q", "")
        campo = self.request.GET.get("campo", "")
        
        if q:
            if campo == "nombre":
                queryset = queryset.filter(nombre__icontains=q)
            elif campo == "segmento":
                queryset = queryset.filter(segmentacion__nombre__icontains=q)
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["segmentaciones"] = Segmentacion.objects.all()
        context["form"] = ClienteForm()
        context["form_action"] = reverse_lazy('clientes-agregar')
        context["q"] = self.request.GET.get("q", "")
        context["campo"] = self.request.GET.get("campo", "")
        context["seg_selected"] = self.request.GET.get("seg", "")
        return context



@method_decorator(superadmin_required, name='dispatch')
class ClienteCreateView(CreateView):
    """
    Vista para crear un cliente desde un modal en la lista de clientes.
    """
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
    """
    Valida de manera AJAX si un correo ya está registrado.

    POST Params:
        - email: correo a validar
        - obj_id: ID del cliente a excluir (para edición)

    Retorna:
        JsonResponse: True si el correo NO existe, False si ya está en uso.
    """
    if request.method == 'POST':
        email = request.POST.get('email')
        obj_id = request.POST.get('obj_id')

        query = Cliente.objects.filter(email=email)
        if obj_id and obj_id != 'null' and obj_id != '':
            query = query.exclude(id=obj_id)

        exists = query.exists()
        return JsonResponse(not exists, safe=False)


@method_decorator(superadmin_required, name='dispatch')
class ClienteUpdateView(UpdateView):
    """
    Vista para editar un cliente desde un modal en la lista de clientes.
    """
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
    """
    Vista para eliminar un cliente.
    """
    model = Cliente
    template_name = 'clientes/form.html'
    success_url = reverse_lazy('clientes')

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Cliente eliminado correctamente.")
        return super().delete(request, *args, **kwargs)


@method_decorator(superadmin_required, name='dispatch')
class ClienteDesactivateView(UpdateView):
    """
    Vista para desactivar un cliente (cambia estado a 'inactivo').
    """
    model = Cliente
    template_name = 'clientes/form.html'
    success_url = reverse_lazy('clientes')
    fields = []

    def post(self, request, *args, **kwargs):
        cliente = self.get_object()
        cliente.estado = 'inactivo'
        cliente.save()
        messages.success(request, "Cliente desactivado correctamente.")
        return redirect(self.success_url)


@method_decorator(superadmin_required, name='dispatch')
class ClienteActivateView(UpdateView):
    """
    Vista para activar un cliente (cambia estado a 'activo').
    """
    model = Cliente
    template_name = 'clientes/form.html'
    success_url = reverse_lazy('clientes')
    fields = []

    def post(self, request, *args, **kwargs):
        cliente = self.get_object()
        cliente.estado = 'activo'
        cliente.save()
        messages.success(request, "Cliente activado correctamente.")
        return redirect(self.success_url)


@superadmin_required
def cliente_detalle(request, pk):
    """
    Devuelve los detalles de un cliente en formato JSON.

    Útil para cargar datos en modales de edición.

    Args:
        pk (int): ID del cliente

    Returns:
        JsonResponse: Diccionario con los datos del cliente
    """
    cliente = get_object_or_404(Cliente, pk=pk)
    return JsonResponse({
        "nombre": cliente.nombre,
        "email": cliente.email,
        "telefono": cliente.telefono,
        "segmentacion": cliente.segmentacion.id if cliente.segmentacion else None,
        "estado": cliente.estado,
    })
