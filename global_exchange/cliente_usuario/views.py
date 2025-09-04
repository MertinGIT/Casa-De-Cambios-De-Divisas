# views.py
from functools import wraps
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from usuarios.models import CustomUser
from .forms import ClienteUsuariosForm
from clientes.models import Cliente


# Solo superadmin
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
            if request.user.is_superuser or request.user.groups.filter(name='ADMIN').exists():
                return view_func(request, *args, **kwargs)
            else:
                # Usuario normal no tiene acceso
                return redirect('home')
        return redirect('login')
    return _wrapped_view

# Listar asignaciones
@superadmin_required
def cliente_usuarios_lista(request):
    """
    Vista que muestra la lista de asignaciones entre usuarios y clientes.

    Contexto enviado a la plantilla:
      - ``usuarios_clientes``: asignaciones existentes.
      - ``usuarios``: lista de usuarios registrados.
      - ``clientes``: lista de clientes disponibles.
    """
    clientes = Cliente.objects.all().order_by('-id')
    usuarios = CustomUser.objects.all()
    form = ClienteUsuariosForm()
    
    return render(request, 'lista.html',{
        'usuarios': usuarios,
        'clientes': clientes,
        'form': form,
    })


# Editar asignación
@superadmin_required
def editar_cliente_usuario(request, id):
    """
    Vista que permite editar una asignación existente.

    - Permite cambiar el usuario, el cliente y el rol asociados.
    - Si no se selecciona rol, este se deja en ``None``.
    """
    cliente = get_object_or_404(Cliente, id=id)

    if request.method == "POST":
        form = ClienteUsuariosForm(request.POST, instance=cliente)
        if form.is_valid():
            form.save()
            return redirect("cliente_usuario")
    else:
        form = ClienteUsuariosForm(instance=cliente)
    usuarios_all = CustomUser.objects.all().order_by('username')
    usuarios_asignados = list(cliente.usuarios.values_list('id', flat=True))
    return render(request, "lista.html", {
        "form": form,
        "usuarios": usuarios_all,
        "usuarios_asignados": usuarios_asignados,
        "show_modal": True,
        "modal_type": "edit",
        "obj_id": cliente.id,
    })


# Vista para obtener datos de un rol via AJAX (para llenar el modal de edición)
@superadmin_required
def cliente_usuario_detalle(request, pk):
    
    cliente = get_object_or_404(Cliente, pk=pk)
    usuarios_ids = list(map(str, cliente.usuarios.values_list('id', flat=True)))
    return JsonResponse({
        "usuarios": usuarios_ids,
        "modal_title": "Editar Asignación"
    })