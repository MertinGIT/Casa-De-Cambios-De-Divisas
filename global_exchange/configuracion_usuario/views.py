from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from clientes.models import Cliente
from cliente_usuario.models import Usuario_Cliente

def configuracion_view_usuario(request):
    # === Segmentación según usuario ===
    descuento = 0
    segmento_nombre = "Sin segmentación"
    # === SEGMENTACIÓN SEGÚN USUARIO ===
    if request.user.is_authenticated:  # solo si está logueado
        clientes_asociados, cliente_operativo = obtener_clientes_usuario(request.user, request)

        if (cliente_operativo and cliente_operativo.segmentacion and cliente_operativo.segmentacion.estado == "activo"):
            descuento = float(cliente_operativo.segmentacion.descuento)
        
    return render(request, 'configuracion_usuario/configuracion_home_usuario.html',{"segmento": segmento_nombre,
        "clientes_asociados": clientes_asociados,
        "cliente_operativo": cliente_operativo,'descuento': descuento,})


def obtener_clientes_usuario(user,request):
    """
    Devuelve:
        - clientes_asociados: lista de todos los clientes asociados al usuario
        - cliente_operativo: cliente actualmente seleccionado (desde sesión si existe)
    """

     # Solo clientes activos
    usuarios_clientes = (
        Usuario_Cliente.objects
        .select_related("id_cliente__segmentacion")
        .filter(id_usuario=user, id_cliente__estado="activo")
    )
    
    clientes_asociados = [uc.id_cliente for uc in usuarios_clientes if uc.id_cliente]
    cliente_operativo = None

    # Tomar de la sesión si existe
    if request and request.session.get('cliente_operativo_id'):
        cliente_operativo = next((c for c in clientes_asociados if c.id == request.session['cliente_operativo_id']), None)

    # Si no hay sesión o ID no válido, tomar el primero
    if not cliente_operativo and clientes_asociados:
        cliente_operativo = clientes_asociados[0]

    return clientes_asociados, cliente_operativo

@login_required
def set_cliente_operativo(request):
    """
    Establece en sesión el cliente operativo para el usuario autenticado.

    Permite cambiar el cliente activo en el contexto de las operaciones.
    Devuelve información de segmentación y descuento del cliente seleccionado.

    :param request: Objeto HTTP con la información de la petición.
    :type request: HttpRequest
    :return: JsonResponse con los datos del cliente operativo o error.
    :rtype: JsonResponse
    """
    cliente_id = request.POST.get('cliente_id')
    if cliente_id:
        try:
            cliente = Cliente.objects.select_related("segmentacion").get(
                pk=cliente_id, estado="activo"
            )
            request.session['cliente_operativo_id'] = cliente.id
            segmento_nombre = None
            descuento = 0
            if cliente.segmentacion and cliente.segmentacion.estado == "activo":
                segmento_nombre = cliente.segmentacion.nombre
                descuento = float(cliente.segmentacion.descuento or 0)
            return JsonResponse({
                "success": True,
                "segmento": segmento_nombre,
                "descuento": descuento,
                "cliente_nombre": cliente.nombre,
                "cliente_email": cliente.email
            })
        except Cliente.DoesNotExist:
            return JsonResponse({"success": False, "error": "Cliente no encontrado"}, status=404)
    return JsonResponse({"success": False, "error": "Petición inválida"}, status=400)

