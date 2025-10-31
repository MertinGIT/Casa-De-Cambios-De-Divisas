from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction as db_transaction
from django.db.models import Sum, Q
from clientes.models import Cliente
from operaciones.models import Transaccion
from .forms import LoginATMForm, SeleccionarTransaccionForm
from tauser.models import StockTauser, Localidad
from tauser.utils import GestorStockTauser
from decimal import Decimal
from django.utils import timezone
from usuarios.models import CustomUser  # ✅ Importar CustomUser
from cliente_usuario.models import Usuario_Cliente  # ✅ Importar relación usuario-cliente
from functools import wraps


# ==================== SESIÓN ATM ====================

# 1. Selección de localidad
def atm_seleccionar_localidad(request):
    """
    Paso 1: Selección de la localidad (TAUSER) antes del inicio de sesión.

    Permite al usuario seleccionar el TAUSER (localidad) con el que desea operar.
    - Si el método es POST: guarda la localidad seleccionada en la sesión y redirige al login.
    - Si el método es GET: muestra todas las localidades activas disponibles.

    Args:
        request (HttpRequest): Solicitud HTTP del cliente.

    Returns:
        HttpResponse: Renderiza la plantilla de selección de localidad o redirige al login.
    """
    if request.method == 'POST':
        localidad_id = request.POST.get('localidad_id')
        
        if not localidad_id:
            messages.error(request, 'Debe seleccionar una localidad')
            return redirect('atm_seleccionar_localidad')
        
        try:
            localidad = Localidad.objects.get(id=localidad_id, activo=True)
            
            # Guardar localidad en sesión ATM
            request.session['atm_localidad_id'] = localidad.id
            request.session['atm_localidad_nombre'] = localidad.nombre
            
            messages.success(request, f'TAUSER seleccionado: {localidad.nombre}')
            return redirect('atm_login')
            
        except Localidad.DoesNotExist:
            messages.error(request, 'Localidad no válida')
            return redirect('atm_seleccionar_localidad')
    
    localidades = Localidad.objects.filter(activo=True).order_by('nombre')
    
    context = {
        'localidades': localidades,
    }
    
    return render(request, 'tauser/seleccionar_localidad.html', context)


# 2. Login
def atm_login(request):
    """
    Vista de inicio de sesión del terminal de autoservicio (ATM).

    Permite al cliente autenticarse ingresando su número de cédula.
    Requiere que previamente se haya seleccionado una localidad TAUSER.

    Args:
        request (HttpRequest): Solicitud HTTP del cliente.

    Returns:
        HttpResponse: Renderiza el formulario de login o redirige al dashboard.
    """
    # Verificar que haya seleccionado una localidad
    localidad_id = request.session.get('atm_localidad_id')
    if not localidad_id:
        messages.warning(request, 'Primero debe seleccionar un TAUSER')
        return redirect('atm_seleccionar_localidad')
    
    # Si ya hay sesión ATM activa con usuario y cliente, redirigir al dashboard
    if request.session.get('atm_user_id') and request.session.get('atm_cliente_id'):
        return redirect('atm_dashboard')
    
    # Si solo tiene usuario pero no cliente, redirigir a seleccionar cliente
    if request.session.get('atm_user_id') and not request.session.get('atm_cliente_id'):
        return redirect('atm_seleccionar_cliente')
    
    localidad_nombre = request.session.get('atm_localidad_nombre', 'TAUSER')
    
    if request.method == 'POST':
        cedula = request.POST.get('cedula', '').strip()
        password = request.POST.get('password', '')
        
        if not cedula or not password:
            messages.error(request, '❌ Debes completar todos los campos')
            return render(request, 'tauser/login_tauser.html', {'localidad_nombre': localidad_nombre})
        
        try:
            # ✅ Buscar usuario por cédula en CustomUser
            user = CustomUser.objects.get(cedula=cedula)
            
            # ✅ Verificar contraseña
            if user.check_password(password):
                # ✅ Crear sesión ATM independiente (NO usar django.contrib.auth.login)
                request.session['atm_user_id'] = user.id
                request.session['atm_username'] = user.username
                request.session['atm_cedula'] = user.cedula
                request.session['is_atm_session'] = True
                
                print(f"✅ Login ATM exitoso: {user.username} (Cédula: {cedula})", flush=True)
                
                messages.success(request, f'✓ Bienvenido {user.username}')
                return redirect('atm_seleccionar_cliente')
            else:
                messages.error(request, '❌ Contraseña incorrecta')
                print(f"❌ Contraseña incorrecta para cédula: {cedula}", flush=True)
                
        except CustomUser.DoesNotExist:
            messages.error(request, '❌ Usuario no encontrado')
            print(f"❌ Usuario no encontrado con cédula: {cedula}", flush=True)
    
    context = {
        'localidad_nombre': localidad_nombre,
    }
    
    return render(request, 'tauser/login_tauser.html', context)


# 3. Seleccionar cliente ✅ ESTA FUNCIÓN DEBE EXISTIR
def atm_seleccionar_cliente(request):
    """
    Vista para seleccionar el cliente con el cual operará el usuario en el ATM.

    Esta función valida que el usuario ATM esté autenticado mediante sesión y luego
    obtiene los clientes asociados al mismo. El usuario debe elegir un cliente activo
    para continuar operando dentro del sistema ATM.

    Flujo:
        1. Verifica que exista un usuario ATM autenticado en la sesión.
        2. Obtiene los clientes asociados al usuario y filtra solo los activos.
        3. Si no posee clientes asignados, se finaliza la sesión ATM.
        4. Si es una solicitud POST, valida el cliente seleccionado:
            - Verifica que el cliente exista y esté activo.
            - Verifica que pertenezca al usuario ATM.
            - Guarda los datos del cliente seleccionado en la sesión.
        5. Si es GET, muestra la vista para seleccionar el cliente.

    Variables de sesión utilizadas:
        - atm_user_id: ID del usuario ATM autenticado.
        - atm_localidad_nombre: Nombre de la localidad asignada (por defecto "TAUSER").
        - atm_cliente_id: ID del cliente seleccionado una vez validado.
        - atm_cliente_nombre: Nombre del cliente seleccionado.
        - atm_cliente_ruc: RUC del cliente seleccionado.
        - atm_cliente_cedula: Cédula del cliente seleccionado.

    Mensajes mostrados:
        - Advertencia si no hay sesión ATM iniciada.
        - Error si no posee clientes asignados o selecciona uno inválido.
        - Confirmación exitosa al seleccionar el cliente.

    Redirecciones:
        - `atm_login`: Si no existe sesión válida.
        - `atm_logout`: Si no tiene clientes asociados.
        - `atm_seleccionar_cliente`: Si hay error de selección.
        - `atm_dashboard`: Si la selección de cliente es exitosa.

    Retorno:
        Renderiza la plantilla 'tauser/seleccionar_cliente.html' con:
            - user: Usuario autenticado.
            - clientes: Lista de clientes asociados activos.
            - localidad_nombre: Nombre de la localidad asignada.
    """
    atm_user_id = request.session.get('atm_user_id')
    localidad_nombre = request.session.get('atm_localidad_nombre', 'TAUSER')
    
    if not atm_user_id:
        messages.warning(request, 'Debes iniciar sesión primero')
        return redirect('atm_login')
    
    try:
        user = CustomUser.objects.get(id=atm_user_id)
        
        # ✅ Obtener clientes asociados al usuario
        usuarios_clientes = Usuario_Cliente.objects.filter(
            id_usuario=user,
            id_cliente__estado="activo"
        ).select_related('id_cliente')
        
        clientes_disponibles = [uc.id_cliente for uc in usuarios_clientes]
        
        if not clientes_disponibles:
            messages.error(request, '❌ No tienes clientes asociados. Contacta al administrador.')
            return redirect('atm_logout')
        
        if request.method == 'POST':
            cliente_id = request.POST.get('cliente_id')
            
            if not cliente_id:
                messages.error(request, 'Debes seleccionar un cliente')
                return redirect('atm_seleccionar_cliente')
            
            try:
                cliente = Cliente.objects.get(id=cliente_id, estado="activo")
                
                # Validar que el cliente pertenezca al usuario
                if cliente not in clientes_disponibles:
                    messages.error(request, '❌ Cliente no autorizado')
                    return redirect('atm_seleccionar_cliente')
                
                # ✅ Guardar cliente operativo en sesión ATM
                request.session['atm_cliente_id'] = cliente.id
                request.session['atm_cliente_nombre'] = cliente.nombre
                request.session['atm_cliente_ruc'] = cliente.ruc
                request.session['atm_cliente_cedula'] = cliente.cedula
                
                print(f"✅ Cliente seleccionado: {cliente.nombre} (ID: {cliente.id})", flush=True)
                
                messages.success(request, f'✓ Operando como: {cliente.nombre}')
                return redirect('atm_dashboard')
                
            except Cliente.DoesNotExist:
                messages.error(request, 'Cliente no encontrado')
                return redirect('atm_seleccionar_cliente')
        
        context = {
            'user': user,
            'clientes': clientes_disponibles,
            'localidad_nombre': localidad_nombre,
        }
        return render(request, 'tauser/seleccionar_cliente.html', context)
        
    except CustomUser.DoesNotExist:
        messages.error(request, 'Sesión inválida')
        return redirect('atm_login')


# 4. Dashboard
def atm_dashboard(request):
    """
    Dashboard principal del ATM.

    Muestra el menú principal de operaciones del cliente autenticado.
    Si la sesión es inválida, redirige a la selección de localidad.

    Args:
        request (HttpRequest): Solicitud HTTP del cliente.

    Returns:
        HttpResponse: Renderiza la vista de menú principal.
    """
    atm_user_id = request.session.get('atm_user_id')
    atm_cliente_id = request.session.get('atm_cliente_id')
    localidad_id = request.session.get('atm_localidad_id')
    
    if not atm_user_id or not atm_cliente_id or not localidad_id:
        messages.warning(request, 'Sesión incompleta')
        return redirect('atm_seleccionar_localidad')
    
    try:
        user = CustomUser.objects.get(id=atm_user_id)
        cliente = Cliente.objects.get(id=atm_cliente_id)
        localidad = Localidad.objects.get(id=localidad_id)
        
        context = {
            'user': user,
            'cliente': cliente,
            'localidad': localidad,
        }
        
        return render(request, 'tauser/menu.html', context)
    
    except (CustomUser.DoesNotExist, Cliente.DoesNotExist, Localidad.DoesNotExist):
        request.session.flush()
        messages.error(request, 'Sesión inválida')
        return redirect('atm_seleccionar_localidad')


# 5. Logout
def atm_logout(request):
    """
    Cierre de sesión en el terminal TAUSER.

    Elimina todas las variables de sesión del ATM y redirige a la selección de localidad.

    Args:
        request (HttpRequest): Solicitud HTTP del cliente.

    Returns:
        HttpResponseRedirect: Redirige al inicio del ATM.
    """
    username = request.session.get('atm_username', 'Usuario')
    
    # ✅ Eliminar solo las claves de sesión ATM
    keys_to_delete = [
        'atm_user_id',
        'atm_username',
        'atm_cedula',
        'atm_cliente_id',
        'atm_cliente_nombre',
        'atm_cliente_ruc',
        'atm_cliente_cedula',
        'is_atm_session',
        'atm_localidad_id',
        'atm_localidad_nombre'
    ]
    
    for key in keys_to_delete:
        if key in request.session:
            del request.session[key]
    
    print(f"🔴 Logout ATM: {username}", flush=True)
    
    messages.success(request, '✓ Sesión del ATM cerrada correctamente')
    return redirect('atm_seleccionar_localidad')


# ==================== DECORADOR DE PROTECCIÓN ====================

def require_atm_session(view_func):
    """
    Decorador para proteger vistas que requieren sesión ATM activa.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        atm_user_id = request.session.get('atm_user_id')
        atm_cliente_id = request.session.get('atm_cliente_id')
        localidad_id = request.session.get('atm_localidad_id')
        
        if not atm_user_id:
            messages.warning(request, 'Debes iniciar sesión en el ATM')
            return redirect('atm_login')
        
        if not atm_cliente_id:
            messages.warning(request, 'Debes seleccionar un cliente')
            return redirect('atm_seleccionar_cliente')
        
        if not localidad_id:
            messages.warning(request, 'Debes seleccionar una localidad')
            return redirect('atm_seleccionar_localidad')
        
        return view_func(request, *args, **kwargs)
    return wrapper


# ==================== VISTAS PROTEGIDAS ====================

@require_atm_session
def atm_transacciones(request):
    """
    Muestra el historial de transacciones del cliente.

    Recupera las transacciones realizadas por el cliente actual en el sistema,
    ordenadas por fecha descendente.

    Args:
        request (HttpRequest): Solicitud HTTP del cliente.

    Returns:
        HttpResponse: Renderiza la vista de historial de transacciones.
    """
    cliente_id = request.session.get('atm_cliente_id')
    localidad_id = request.session.get('atm_localidad_id')
    
    try:
        cliente = Cliente.objects.get(id=cliente_id)
        localidad = Localidad.objects.get(id=localidad_id)
        
        transacciones = Transaccion.objects.filter(
            cliente=cliente
        ).select_related(
            'moneda_origen', 
            'moneda_destino', 
            'tasa_ref'
        ).order_by('-fecha')
        
        context = {
            'cliente': cliente,
            'transacciones': transacciones,
            'localidad': localidad,
        }
        
        return render(request, 'tauser/transacciones.html', context)
    
    except (Cliente.DoesNotExist, Localidad.DoesNotExist):
        request.session.flush()
        messages.error(request, 'Sesión inválida')
        return redirect('atm_seleccionar_localidad')


@require_atm_session
def atm_depositar(request):
    """
    Procesa depósitos en efectivo del cliente en el TAUSER.

    - Muestra las transacciones pendientes de pago en efectivo.
    - Permite registrar el depósito físico y actualizar el saldo del cliente.
    - Si el medio de acreditación es "TAUSER", el saldo se incrementa automáticamente.

    Args:
        request (HttpRequest): Solicitud HTTP del cliente.

    Returns:
        HttpResponse: Renderiza la vista de depósito o redirige tras completar el proceso.
    """
    cliente_id = request.session.get('atm_cliente_id')
    localidad_id = request.session.get('atm_localidad_id')
    
    try:
        cliente = Cliente.objects.get(id=cliente_id)
        localidad = Localidad.objects.get(id=localidad_id)

        transacciones_pendientes = Transaccion.objects.filter(
            cliente=cliente,
            estado='pendiente',
            metodo_pago_id=1  # Efectivo
        ).select_related('moneda_origen', 'moneda_destino', 'metodo_pago').order_by('-fecha')

        # ✅ Mostrar el monto_recibir guardado en la transacción
        transacciones_con_calculo = []
        for trans in transacciones_pendientes:
            # Usar el monto_recibir que está guardado en la transacción
            monto_recibir = trans.monto_recibir if trans.monto_recibir else Decimal('0')
            moneda_recibir = trans.moneda_destino
            
            transacciones_con_calculo.append({
                'transaccion': trans,
                'monto_recibir': f"{float(monto_recibir):.2f}",
                'moneda_recibir': moneda_recibir
            })

        if request.method == 'POST':
            transaccion_id = request.POST.get('transaccion_id')
            
            if not transaccion_id:
                messages.error(request, 'No se especificó la transacción')
                return redirect('atm_depositar')
            
            transaccion = get_object_or_404(
                Transaccion,
                id=transaccion_id,
                cliente=cliente,
                estado='pendiente'
            )

            with db_transaction.atomic():
                # Registrar depósito en stock
                try:
                    moneda_deposito = transaccion.moneda_origen
                    monto_deposito = Decimal(str(transaccion.monto))
                    
                    GestorStockTauser.registrar_deposito_efectivo(
                        monto=float(monto_deposito),
                        moneda=moneda_deposito,
                        localidad=localidad
                    )
                    
                except Exception as e:
                    print(f"Error al registrar depósito: {e}")
                    messages.error(request, f'Error al procesar el depósito: {str(e)}')
                    return redirect('atm_depositar')

                es_tauser = (
                    transaccion.medio_acreditacion is not None 
                    and transaccion.medio_acreditacion.entidad is not None 
                    and transaccion.medio_acreditacion.entidad.nombre.strip().lower() == "tauser"
                )

                
                if es_tauser:
                    from clientes.models import SaldoCliente
                    
                    # ✅ Usar el monto_recibir guardado en la transacción
                    moneda_recibir = transaccion.moneda_destino
                    monto_recibir = transaccion.monto_recibir if transaccion.monto_recibir else Decimal('0')
                    
                    # Obtener o crear el saldo
                    saldo, created = SaldoCliente.objects.get_or_create(
                        cliente=cliente,
                        moneda=moneda_recibir,
                        localidad=localidad,
                        defaults={'saldo': Decimal('0')}
                    )
                    
                    # Incrementar saldo con el monto exacto que vio el cliente
                    saldo_anterior = saldo.saldo
                    saldo.saldo += monto_recibir
                    saldo.save()
                    
                    print(f"✅ Saldo actualizado después del depósito:", flush=True)
                    print(f"   Cliente: {cliente.nombre}", flush=True)
                    print(f"   Moneda: {moneda_recibir.abreviacion}", flush=True)
                    print(f"   Saldo anterior: {saldo_anterior}", flush=True)
                    print(f"   Monto agregado: {monto_recibir}", flush=True)
                    print(f"   Saldo nuevo: {saldo.saldo}", flush=True)

                # Cambiar estado a confirmada
                transaccion.estado = 'confirmada'
                transaccion.save(update_fields=['estado'])

                # ✅ 5. GENERAR FACTURA (SIN DUPLICAR RANGOS)
                try:
                    from facturacion.services import FacturaSeguraService
                    
                    print(f"🧾 Generando factura para transacción #{transaccion.id}", flush=True)
                    
                    # ✅ VERIFICAR SI YA EXISTE UNA FACTURA PARA ESTA TRANSACCIÓN
                    from facturacion.models import Factura
                    
                    factura_existente = Factura.objects.filter(transaccion=transaccion).first()
                    
                    if factura_existente:
                        print(f"⚠️ Factura ya existe: {factura_existente.numero_factura}", flush=True)
                        factura = factura_existente
                    else:
                        # ✅ Generar nueva factura SOLO si no existe
                        # Construir los datos esperados
                        transaccion_data = {
                            'monto': float(transaccion.monto),
                            'moneda_origen': transaccion.moneda_origen.abreviacion,
                            'moneda_destino': transaccion.moneda_destino.abreviacion,
                            'tasa_usada': float(transaccion.tasa_ref.valor) if getattr(transaccion, 'tasa_ref', None) else None,
                            'referencia': transaccion.id,
                            'metodo_pago': transaccion.metodo_pago.nombre if getattr(transaccion, 'metodo_pago', None) else None,
                            'tipo': transaccion.tipo,
                            'moneda': transaccion.moneda_destino.abreviacion,  # 👈 ESTE es el campo que faltaba
                        }

                        cliente_data = {
                            'nombre_completo': cliente.nombre,
                            'email': cliente.email,
                            'cedula': cliente.cedula,
                            'ruc': cliente.ruc,
                            'dv_ruc': getattr(cliente, 'dv_ruc', None),
                        }

                        # Llamada corregida
                        factura = FacturaSeguraService.generar_factura_cambio(
                            transaccion_data,
                            cliente_data,
                            usuario=request.user if getattr(request, 'user', None) and request.user.is_authenticated else None
                        )

                        print(f"✅ Factura generada: {factura.numero_factura}", flush=True)
                    
                except Exception as e:
                    # ❌ NO FALLAR si hay error en facturación
                    print(f"⚠️ Error al generar factura (continuando): {str(e)}", flush=True)
                    import traceback
                    traceback.print_exc()
                    # NO hacer return aquí, continuar con el depósito

                # ✅ 6. Mensaje de éxito
                mensaje_exito = f'✓ Depósito exitoso: {transaccion.monto:.2f} {transaccion.moneda_origen.abreviacion}'
                
                if es_tauser:
                    # Formatear saldo según tipo de moneda
                    if moneda_recibir.abreviacion.upper() == 'PYG':
                        saldo_formateado = f"{int(saldo.saldo):,}"
                    else:
                        saldo_formateado = f"{float(saldo.saldo):,.2f}"
                    
                    mensaje_exito += f'. Saldo disponible: {saldo_formateado} {moneda_recibir.abreviacion}'

            messages.success(request, mensaje_exito)
            return redirect('atm_depositar')

        context = {
            'cliente': cliente,
            'localidad': localidad,
            'transacciones': transacciones_con_calculo,
        }
        return render(request, 'tauser/depositar.html', context)

    except (Cliente.DoesNotExist, Localidad.DoesNotExist):
        request.session.flush()
        messages.error(request, 'Sesión inválida')
        return redirect('atm_seleccionar_localidad')


@require_atm_session
def atm_extraer(request):
    """
    Permite la extracción (retiro) de dinero del saldo TAUSER del cliente.

    - Opción de retiro total automático o retiro parcial personalizado.
    - Calcula los billetes óptimos según el stock disponible.
    - Actualiza el saldo del cliente y el stock de billetes de la localidad.

    Args:
        request (HttpRequest): Solicitud HTTP del cliente.

    Returns:
        HttpResponse: Renderiza la vista de extracción o redirige tras confirmar el retiro.
    """
    cliente_id = request.session.get('atm_cliente_id')
    localidad_id = request.session.get('atm_localidad_id')
    
    try:
        cliente = Cliente.objects.get(id=cliente_id)
        localidad = Localidad.objects.get(id=localidad_id)
        
        # ✅ Obtener saldos del cliente en Tauser
        from clientes.models import SaldoCliente
        
        saldos_cliente = SaldoCliente.objects.filter(
            cliente=cliente,
            localidad=localidad,
            saldo__gt=0
        ).select_related('moneda').order_by('-saldo')
        
        monedas_con_detalle = []
        
        for saldo_obj in saldos_cliente:
            moneda = saldo_obj.moneda
            saldo_disponible = saldo_obj.saldo
            
            # ✅ Obtener stock de billetes disponibles en el ATM
            stock_billetes = StockTauser.objects.filter(
                localidad=localidad,
                denominacion__moneda=moneda,
                cantidad__gt=0
            ).select_related('denominacion').order_by('-denominacion__valor')
            
            billetes_disponibles = []
            for stock in stock_billetes:
                billetes_disponibles.append({
                    'denominacion_id': stock.denominacion.id,
                    'valor': float(stock.denominacion.valor),
                    'cantidad_disponible': stock.cantidad,
                    'moneda_abrev': stock.denominacion.moneda.abreviacion
                })
            
            # Calcular billetes óptimos para retiro total
            try:
                billetes_optimo, monto_entregado, diferencia, posible = GestorStockTauser.calcular_billetes_optimo(
                    float(saldo_disponible),
                    moneda,
                    localidad
                )
            except Exception as e:
                print(f"ERROR al calcular billetes: {e}")
                billetes_optimo = {}
                monto_entregado = 0
                diferencia = float(saldo_disponible)
                posible = False
            
            # Detalles de billetes para retiro total
            detalles_billetes = []
            for denom_id, cantidad in billetes_optimo.items():
                try:
                    stock = StockTauser.objects.select_related('denominacion').get(denominacion_id=denom_id,localidad=localidad)
                    detalles_billetes.append({
                        'denominacion_id': denom_id,
                        'valor': float(stock.denominacion.valor),
                        'cantidad': cantidad,
                        'subtotal': float(stock.denominacion.valor) * cantidad,
                    })
                except StockTauser.DoesNotExist:
                    continue
            
            # Ordenar por valor descendente
            detalles_billetes.sort(key=lambda x: x['valor'], reverse=True)
            
            print(f"💰 Moneda: {moneda.abreviacion}", flush=True)
            print(f"   Saldo disponible: {float(saldo_disponible)}", flush=True)
            monedas_con_detalle.append({
                'moneda': moneda,
                'saldo_disponible': float(saldo_disponible),
                'billetes_disponibles': billetes_disponibles,
                'billetes_retiro_total': detalles_billetes,
                'monto_entregado': monto_entregado,
                'diferencia': diferencia,
                'posible_efectivo': posible,
                'saldo_obj': saldo_obj
            })
        print("monedas_con_detalle",monedas_con_detalle ,flush=True)
        
        if request.method == 'POST':
            moneda_id = request.POST.get('moneda_id')
            tipo_retiro = request.POST.get('tipo_retiro')  # 'total' o 'parcial'
            
            if not moneda_id:
                messages.error(request, 'Datos incompletos')
                return redirect('atm_extraer')
            
            # Obtener el saldo del cliente
            try:
                saldo_obj = SaldoCliente.objects.select_related('moneda').get(
                    cliente=cliente,
                    moneda_id=moneda_id,
                    localidad=localidad,
                    saldo__gt=0
                )
            except SaldoCliente.DoesNotExist:
                messages.error(request, 'No tienes saldo en esta moneda')
                return redirect('atm_extraer')
            
            moneda = saldo_obj.moneda
            
            # Determinar billetes a entregar
            if tipo_retiro == 'parcial':
                # ✅ RETIRO PARCIAL PERSONALIZADO
                billetes_seleccionados = {}
                monto_total = 0
                
                # Leer las cantidades enviadas desde el formulario
                for key, value in request.POST.items():
                    if key.startswith('billete_'):
                        denom_id = int(key.replace('billete_', ''))
                        cantidad = int(value) if value else 0
                        
                        if cantidad > 0:
                            try:
                                stock = StockTauser.objects.get(denominacion_id=denom_id,localidad=localidad)
                                
                                # Validar stock disponible
                                if cantidad > stock.cantidad:
                                    messages.error(request, f'Stock insuficiente de billetes de {stock.denominacion.valor}')
                                    return redirect('atm_extraer')
                                
                                billetes_seleccionados[denom_id] = cantidad
                                monto_total += float(stock.denominacion.valor) * cantidad
                                
                            except StockTauser.DoesNotExist:
                                messages.error(request, 'Denominación inválida')
                                return redirect('atm_extraer')
                
                # Validar que el monto no exceda el saldo
                if monto_total > float(saldo_obj.saldo):
                    messages.error(request, f'El monto seleccionado ({monto_total:.2f}) excede tu saldo disponible ({float(saldo_obj.saldo):.2f})')
                    return redirect('atm_extraer')
                
                if monto_total == 0:
                    messages.error(request, 'Debes seleccionar al menos un billete')
                    return redirect('atm_extraer')
                
                billetes = billetes_seleccionados
                monto_entregado = monto_total  # ✅ Este es el monto REAL que se entregará
                
                print(f"💵 RETIRO PARCIAL:", flush=True)
                print(f"   Monto solicitado (input): {request.POST.get('monto_solicitado', 'N/A')}", flush=True)
                print(f"   Monto calculado (billetes): {monto_entregado}", flush=True)
                
            else:
                # ✅ RETIRO TOTAL AUTOMÁTICO
                billetes, monto_entregado, diferencia, posible = GestorStockTauser.calcular_billetes_optimo(
                    float(saldo_obj.saldo),
                    moneda,
                    localidad
                )
                
                if monto_entregado == 0:
                    messages.error(request, 'No hay billetes disponibles en este momento')
                    return redirect('atm_extraer')
                
                print(f"💵 RETIRO TOTAL:", flush=True)
                print(f"   Saldo disponible: {float(saldo_obj.saldo)}", flush=True)
                print(f"   Monto entregado: {monto_entregado}", flush=True)
            
            with db_transaction.atomic():
                # ✅ Actualizar stock de billetes
                for denom_id, cantidad in billetes.items():
                    stock = StockTauser.objects.get(denominacion_id=denom_id,localidad=localidad)
                    
                    if stock.cantidad < cantidad:
                        messages.error(request, f'Stock insuficiente de billetes de {stock.denominacion.valor}')
                        return redirect('atm_extraer')
                    
                    #stock.cantidad -= cantidad
                    stock.save()
                    
                    print(f"   📉 Billete {stock.denominacion.valor}: {stock.cantidad + cantidad} → {stock.cantidad}", flush=True)
                
                # ✅ Descontar del saldo del cliente EL MONTO ENTREGADO (no el solicitado)
                saldo_anterior = saldo_obj.saldo
                monto_a_descontar = Decimal(str(monto_entregado))  # ✅ Usar monto_entregado
                
                if monto_a_descontar > saldo_obj.saldo:
                    messages.error(request, 'Error: El monto a entregar excede el saldo disponible')
                    return redirect('atm_extraer')
                
                saldo_obj.saldo -= monto_a_descontar  # ✅ Descontar el monto REAL entregado
                saldo_obj.save()
                
                print(f"✅ Retiro exitoso ({tipo_retiro}):", flush=True)
                print(f"   Cliente: {cliente.nombre}", flush=True)
                print(f"   Moneda: {moneda.abreviacion}", flush=True)
                print(f"   Saldo anterior: {saldo_anterior}", flush=True)
                print(f"   Monto entregado: {monto_entregado}", flush=True)
                print(f"   Saldo nuevo: {saldo_obj.saldo}", flush=True)
                print(f"   Diferencia que queda: {float(saldo_obj.saldo)}", flush=True)
                
                # Formatear mensaje
                if moneda.abreviacion.upper() == 'PYG':
                    mensaje = f'✓ Retiro exitoso en {localidad.nombre}: {int(monto_entregado):,} {moneda.abreviacion}'
                    if saldo_obj.saldo > 0:
                        mensaje += f'. Saldo restante: {int(saldo_obj.saldo):,} {moneda.abreviacion}'
                else:
                    mensaje = f'✓ Retiro exitoso en {localidad.nombre}: {monto_entregado:,.2f} {moneda.abreviacion}'
                    if saldo_obj.saldo > 0:
                        mensaje += f'. Saldo restante: {float(saldo_obj.saldo):,.2f} {moneda.abreviacion}'
                
                messages.success(request, mensaje)
            
            return redirect('atm_extraer')
        
        print("monedas_con_detalle",monedas_con_detalle ,flush=True)
        context = {
            'cliente': cliente,
            'localidad': localidad,
            'monedas': monedas_con_detalle,
        }
        
        return render(request, 'tauser/extraer.html', context)
    
    except(Cliente.DoesNotExist, Localidad.DoesNotExist):
        request.session.flush()
        messages.error(request, 'Sesión inválida')
        return redirect('atm_seleccionar_localidad')
