# views.py
from functools import wraps
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.http import JsonResponse
from .models import Cliente, Segmentacion
from .forms import ClienteForm

def superadmin_required(view_func):
    """
    Decorador que limita el acceso únicamente a usuarios superadministradores.

    - Si el usuario no está autenticado, se lo redirige a ``login``.
    - Si el usuario está autenticado pero no es superadmin, se lo redirige a ``home``.
    - Si el usuario es superadmin, se ejecuta la vista original.
    """
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
    """
    Vista basada en función que renderiza la página principal de clientes.

    - Utiliza la plantilla ``clientes/lista.html``.
    - Requiere que el usuario sea superadmin.
    """
    return render(request, 'clientes/lista.html')


@method_decorator(superadmin_required, name='dispatch')
class ClienteListView(ListView):
    """
    Vista basada en clase que lista todos los clientes.

    Atributos:
        - ``model``: modelo ``Cliente``.
        - ``template_name``: plantilla usada (``clientes/lista.html``).
        - ``context_object_name``: nombre de la variable en el contexto (``clientes``).
        - ``paginate_by``: cantidad de clientes por página (8).

    Contexto adicional:
        - ``segmentaciones``: lista completa de segmentaciones.
    """
    model = Cliente
    template_name = 'clientes/lista.html'
    context_object_name = 'clientes'
    paginate_by = 8

    def get_queryset(self):
        """Devuelve todos los clientes ordenados por id descendente."""
        return Cliente.objects.all().order_by('-id')

    def get_context_data(self, **kwargs):
        """Agrega las segmentaciones al contexto de la vista."""
        context = super().get_context_data(**kwargs)
        context["segmentaciones"] = Segmentacion.objects.all()
        context["form"] = ClienteForm()  # formulario vacío para el modal
        context["form_action"] = reverse_lazy('clientesAgregar')
        return context


@method_decorator(superadmin_required, name='dispatch')
class ClienteCreateView(CreateView):
    """
    Vista basada en clase que permite crear un nuevo cliente.

    Atributos:
        - ``model``: modelo ``Cliente``.
        - ``template_name``: plantilla usada (``clientes/form.html``).
        - ``fields``: campos editables (``nombre``, ``email``, ``telefono``, ``segmentacion``, ``estado``).
        - ``success_url``: redirección al listado de clientes tras crear.

    Contexto adicional:
        - ``segmentaciones``: lista completa de segmentaciones.
    """
    model = Cliente
    form_class = ClienteForm
    template_name = 'clientes/lista.html'  # ⚡ aquí usamos la lista
    success_url = reverse_lazy('clientes')

    def get_context_data(self, **kwargs):
        """Agrega las segmentaciones al contexto de la vista."""
        context = super().get_context_data(**kwargs)
        context["clientes"] = Cliente.objects.all().order_by('-id')
        context["segmentaciones"] = Segmentacion.objects.all()
        context["modal_title"] = "Agregar Cliente"
        context["form_action"] = reverse_lazy('clientesAgregar')
        return context



@method_decorator(superadmin_required, name='dispatch')
class ClienteUpdateView(UpdateView):
    """
    Vista basada en clase que permite actualizar un cliente existente.

    Atributos:
        - ``model``: modelo ``Cliente``.
        - ``template_name``: plantilla usada (``clientes/form.html``).
        - ``fields``: campos editables (``nombre``, ``email``, ``telefono``, ``segmentacion``, ``estado``).
        - ``success_url``: redirección al listado de clientes tras actualizar.

    Contexto adicional:
        - ``segmentaciones``: lista completa de segmentaciones.
    """
    model = Cliente
    template_name = 'clientes/form.html'
    fields = ['nombre', 'email', 'telefono', 'segmentacion', 'estado']
    success_url = reverse_lazy('clientes')

    def get_context_data(self, **kwargs):
        """Agrega las segmentaciones al contexto de la vista."""
        context = super().get_context_data(**kwargs)
        context["segmentaciones"] = Segmentacion.objects.all()
        return context


@method_decorator(superadmin_required, name='dispatch')
class ClienteDeleteView(DeleteView):
    """
    Vista basada en clase que permite eliminar un cliente.

    Atributos:
        - ``model``: modelo ``Cliente``.
        - ``template_name``: plantilla usada (``clientes/form.html``).
        - ``success_url``: redirección al listado de clientes tras eliminar.

    Notas:
        - Muestra un mensaje de éxito usando ``django.contrib.messages``.
    """
    model = Cliente
    template_name = 'clientes/form.html'
    success_url = reverse_lazy('clientes')

    def delete(self, request, *args, **kwargs):
        """Elimina el cliente y muestra un mensaje de confirmación."""
        messages.success(request, "Cliente eliminado correctamente.")
        return super().delete(request, *args, **kwargs)

def cliente_detalle(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    return JsonResponse({
        "nombre": cliente.nombre,
        "email": cliente.email,
        "telefono": cliente.telefono,
        "segmentacion": cliente.segmentacion_id,
        "estado": cliente.estado,
    })
