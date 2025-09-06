from functools import wraps
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from usuarios.models import CustomUser
from .forms import ClienteUsuariosForm
from clientes.models import Cliente

def cliente_usuarios_lista(request):
    """
    Vista que muestra la lista de asignaciones entre usuarios y clientes.

    Flujo:
    ------
    - Obtiene todos los clientes y usuarios registrados.
    - Inicializa un formulario vacío ``ClienteUsuariosForm`` para crear nuevas asignaciones.
    - Renderiza la plantilla ``lista.html`` con el contexto correspondiente.

    Contexto enviado a la plantilla:
    ---------------------------------
    - ``usuarios_clientes``: asignaciones existentes.
    - ``usuarios``: lista de usuarios registrados.
    - ``clientes``: lista de clientes disponibles.
    - ``form``: formulario para asignar usuarios a clientes.
    """
    clientes = Cliente.objects.all().order_by('-id')
    usuarios = CustomUser.objects.all()
    form = ClienteUsuariosForm()
    
    return render(request, 'lista.html',{
        'usuarios': usuarios,
        'clientes': clientes,
        'form': form,
    })


def editar_cliente_usuario(request, id):
    """
    Vista que permite editar una asignación existente entre un usuario y un cliente.

    Parámetros
    ----------
    id : int
        ID del cliente cuya asignación se desea editar.

    Flujo
    -----
    - Si la petición es ``POST`` y el formulario es válido, guarda los cambios y redirige a la lista de asignaciones.
    - Si la petición no es ``POST`` o hay errores, recarga la plantilla ``lista.html`` con el modal abierto y muestra los errores.
    - Precarga los usuarios asignados al cliente para mostrarlos en el formulario.

    Contexto enviado a la plantilla:
    ---------------------------------
    - ``form``: formulario con los datos del cliente.
    - ``usuarios``: lista de todos los usuarios.
    - ``usuarios_asignados``: IDs de usuarios actualmente asignados al cliente.
    - ``show_modal``: booleano que indica si se debe mostrar el modal.
    - ``modal_type``: indica el tipo de modal, en este caso ``edit``.
    - ``obj_id``: ID del cliente que se está editando.
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


def cliente_usuario_detalle(request, pk):
    """
    Vista que obtiene los usuarios asignados a un cliente para edición mediante AJAX.

    Parámetros
    ----------
    pk : int
        ID del cliente cuya información se desea obtener.

    Retorna
    -------
    JsonResponse
        JSON con la información del cliente:
        - ``usuarios``: lista de IDs de usuarios asignados.
        - ``modal_title``: título del modal, en este caso "Editar Asignación".
    """
    cliente = get_object_or_404(Cliente, pk=pk)
    usuarios_ids = list(map(str, cliente.usuarios.values_list('id', flat=True)))
    return JsonResponse({
        "usuarios": usuarios_ids,
        "modal_title": "Editar Asignación"
    })
