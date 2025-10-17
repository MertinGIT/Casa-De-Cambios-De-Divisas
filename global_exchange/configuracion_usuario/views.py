from django.shortcuts import render,redirect
from django.contrib.auth.decorators import login_required
from clientes.models import Cliente
from cliente_usuario.models import Usuario_Cliente
from django.http import JsonResponse
import json
def configuracion_view_usuario(request):
    """    
    Renderiza la página principal de configuración del usuario autenticado, 
    mostrando su cliente operativo, segmento y descuento correspondiente.

    Parámetros:
        request (HttpRequest): Objeto HTTP con la información de la petición.

    Devuelve:
        Renderiza la plantilla 'configuracion_usuario/configuracion_home_usuario.html' con el contexto:
            - segmento: nombre del segmento del cliente operativo (o “Sin segmentación”).
            - clientes_asociados: lista de clientes vinculados al usuario.
            - cliente_operativo: cliente actualmente seleccionado.
            - descuento: porcentaje de descuento del segmento, si aplica.

    Tipo del valor devuelto:
        HttpResponse
    """
    # === Segmentación según usuario ===
    descuento = 0
    segmento_nombre = "Sin segmentación"
    # === SEGMENTACIÓN SEGÚN USUARIO ===
    if request.user.is_authenticated:  # solo si está logueado
        clientes_asociados, cliente_operativo = obtener_clientes_usuario(request.user, request)

        if (cliente_operativo and cliente_operativo.segmentacion and cliente_operativo.segmentacion.estado == "activo"):
            descuento = float(cliente_operativo.segmentacion.descuento)
            segmento_nombre = cliente_operativo.segmentacion.nombre
        
    return render(request, 'configuracion_usuario/configuracion_home_usuario.html',{
        "segmento": segmento_nombre,
        "clientes_asociados": clientes_asociados,
        "cliente_operativo": cliente_operativo,'descuento': descuento,
        })


def obtener_clientes_usuario(user,request):
    """    
    Devuelve los clientes asociados a un usuario autenticado y determina cuál es el cliente operativo actual.

    Devuelve:
        clientes_asociados: lista de todos los clientes asociados al usuario.
        cliente_operativo: cliente actualmente seleccionado (desde sesión si existe).

    Tipo del valor devuelto:
        tuple (list[Cliente], Cliente | None)
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

    Parámetros:
        request (HttpRequest): Objeto HTTP con la información de la petición.

    Devuelve:
        JsonResponse con los datos del cliente operativo o error.

    Tipo del valor devuelto:
        JsonResponse
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

@login_required
def mfa_configuration(request):
    """    
    Configuración de autenticación multifactor (MFA) para el usuario autenticado.

    Permite activar o desactivar la autenticación multifactor desde una petición 
    AJAX o POST normal, y muestra información de segmentación del cliente operativo.

    Parámetros:
        request (HttpRequest): Objeto HTTP con la información de la petición.

    Devuelve:
        - Si es una petición AJAX POST: JsonResponse con el resultado de la actualización.
        - Si es una petición POST normal: redirección a la vista de configuración MFA.
        - Si es una petición GET: renderiza la plantilla 'configuracion_usuario/mfa_configuration.html'.

    Tipo del valor devuelto:
        JsonResponse | HttpResponseRedirect | HttpResponse
    """
    user = request.user

    segmento_nombre = "Sin Segmentación"
    descuento=0
    # === SEGMENTACIÓN SEGÚN USUARIO ===
    clientes_asociados, cliente_operativo = obtener_clientes_usuario(request.user,request)
    if cliente_operativo and cliente_operativo.segmentacion and cliente_operativo.segmentacion.estado == "activo":
        segmento_nombre = cliente_operativo.segmentacion.nombre
        if cliente_operativo.segmentacion.descuento:
            descuento = float(cliente_operativo.segmentacion.descuento)

    print(f"\n=== MFA Configuration View ===")
    print(f"Método: {request.method}")
    print(f"Usuario: {user.username}")
    print(f"MFA actual en BD: {user.mfa_transacciones}")

    # Manejo de petición AJAX POST
    if request.method == "POST":
        print(f"Es AJAX: {request.headers.get('X-Requested-With') == 'XMLHttpRequest'}")
        print(f"POST data: {request.POST}")
        
        # Verificar si es una petición AJAX
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            try:
                # Obtener el valor del parámetro
                mfa_valor = request.POST.get("mfa_transacciones", "off")
                mfa_estado = mfa_valor == "on"
                
                print(f"Valor recibido: '{mfa_valor}'")
                print(f"Nuevo estado MFA: {mfa_estado}")
                
                # Guardar en la base de datos
                user.mfa_transacciones = mfa_estado
                user.save()
                
                # Verificar que se guardó
                user.refresh_from_db()
                print(f"MFA guardado en BD: {user.mfa_transacciones}")
                
                return JsonResponse({
                    "success": True,
                    "mfa_enabled": mfa_estado,
                    "message": "Configuración actualizada exitosamente"
                })
            except Exception as e:
                print(f"ERROR: {str(e)}")
                import traceback
                traceback.print_exc()
                return JsonResponse({
                    "success": False,
                    "error": str(e)
                }, status=500)
        else:
            # Petición POST normal (sin AJAX)
            mfa_valor = request.POST.get("mfa_transacciones", "off")
            mfa_estado = mfa_valor == "on"
            user.mfa_transacciones = mfa_estado
            user.save()
            print(f"POST normal - MFA guardado: {mfa_estado}")
            return redirect('mfa_configuration')

    # GET request - renderizar template
    print(f"Renderizando template con MFA: {user.mfa_transacciones}")
    return render(request, "configuracion_usuario/mfa_configuration.html", {
        "user": user,
        "segmento": segmento_nombre,
        "clientes_asociados": clientes_asociados,
        "cliente_operativo": cliente_operativo,'descuento': descuento
    })

