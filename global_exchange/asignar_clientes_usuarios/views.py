"""# views.py
from functools import wraps
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from usuarios.models import CustomUser
from .models import Usuario_Rol_Cliente
from clientes.models import Cliente
from django.contrib.auth.models import Group


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
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            else:
                # Usuario normal no tiene acceso
                return redirect('home')
        return redirect('login')
    return _wrapped_view

# Listar asignaciones
@superadmin_required
def lista_usuarios_roles(request):
    """
    Vista que muestra la lista de asignaciones entre usuarios, clientes y roles.

    Contexto enviado a la plantilla:
      - ``usuarios_roles``: asignaciones existentes.
      - ``usuarios``: lista de usuarios registrados.
      - ``clientes``: lista de clientes disponibles.
      - ``roles``: lista de roles definidos.
    """
    usuarios_roles = Usuario_Rol_Cliente.objects.select_related('id_usuario', 'id_cliente')
    usuarios = CustomUser.objects.all()
    clientes = Cliente.objects.all()
    roles = Group.objects.all()  

    context = {
        'usuarios_roles': usuarios_roles,
        'usuarios': usuarios,
        'clientes': clientes,
        'roles': roles,
    }
    return render(request, 'lista.html', context)


# Crear asignación
@superadmin_required
def crear_usuario_rol(request):
    """
    Vista que crea una nueva asignación entre un usuario, un cliente y un rol.

    - Procesa el formulario enviado por POST.
    - Asigna un rol al usuario (o lo deja en ``None`` si no se selecciona).
    - Crea la relación en ``Usuario_Rol_Cliente`` si no existe previamente.
    """
    if request.method == "POST":
        usuario = get_object_or_404(CustomUser, id=request.POST.get('usuario'))
        cliente = get_object_or_404(Cliente, id=request.POST.get('cliente'))

        # Evitar duplicados
        if not Usuario_Rol_Cliente.objects.filter(id_usuario=usuario, id_cliente=cliente).exists():
            Usuario_Rol_Cliente.objects.create(id_usuario=usuario, id_cliente=cliente)

    return redirect('usuarios_roles_lista')



# Editar asignación
@superadmin_required
def editar_usuario_rol(request, id):
    """
    Vista que permite editar una asignación existente.

    - Permite cambiar el usuario, el cliente y el rol asociados.
    - Si no se selecciona rol, este se deja en ``None``.
    """
    asignacion = get_object_or_404(Usuario_Rol_Cliente, id=id)
    if request.method == "POST":
        usuario = get_object_or_404(CustomUser, id=request.POST.get('usuario'))
        cliente = get_object_or_404(Cliente, id=request.POST.get('cliente'))
        # Actualizamos asignación
        asignacion.id_usuario = usuario
        asignacion.id_cliente = cliente
        asignacion.save()

    return redirect('usuarios_roles_lista')

# Eliminar asignación
@superadmin_required
def eliminar_usuario_rol(request, id):
    """
    Vista que elimina una asignación de ``Usuario_Rol_Cliente``.

    - Recibe el ``id`` de la asignación.
    - Borra la relación de la base de datos.
    - Redirige de nuevo a la lista de asignaciones.
    """
    asignacion = get_object_or_404(Usuario_Rol_Cliente, id=id)
    asignacion.delete()
    return redirect('usuarios_roles_lista')
"""