# views.py
from functools import wraps
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from usuarios.models import CustomUser
from .forms import ClienteUsuariosForm
from clientes.models import Cliente

# Listar asignaciones
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
def cliente_usuario_detalle(request, pk):
    
    cliente = get_object_or_404(Cliente, pk=pk)
    usuarios_ids = list(map(str, cliente.usuarios.values_list('id', flat=True)))
    return JsonResponse({
        "usuarios": usuarios_ids,
        "modal_title": "Editar Asignación"
    })