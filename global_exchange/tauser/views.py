from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction as db_transaction
from django.db.models import Sum, Q
from clientes.models import Cliente
from operaciones.models import Transaccion
from .forms import LoginATMForm, SeleccionarTransaccionForm
from tauser.models import StockTauser
from tauser.utils import GestorStockTauser
from decimal import Decimal  # Asegúrate de tener este import al inicio
from django.utils import timezone  # Importar timezone

def atm_login(request):
    """Vista de login para terminal de autoservicio"""
    if request.method == 'POST':
        form = LoginATMForm(request.POST)
        if form.is_valid():
            cedula = form.cleaned_data['cedula']
            try:
                cliente = Cliente.objects.select_related('segmentacion').get(
                    cedula=cedula, 
                    estado='activo'
                )
                # Guardar el cliente en la sesión
                request.session['atm_cliente_id'] = cliente.id
                request.session['atm_cedula'] = cliente.cedula
                request.session['atm_nombre'] = cliente.nombre
                
                messages.success(request, f'Bienvenido {cliente.nombre}')
                return redirect('atm_dashboard')  
                
            except Cliente.DoesNotExist:
                messages.error(request, 'Cliente no encontrado o inactivo')
    else:
        form = LoginATMForm()
    
    return render(request, 'tauser/login_tauser.html', {'form': form})

def atm_dashboard(request):
    """Dashboard principal del ATM - Menú de opciones"""
    cliente_id = request.session.get('atm_cliente_id')
    if not cliente_id:
        return redirect('atm_login')
    
    try:
        cliente = Cliente.objects.select_related('segmentacion').get(id=cliente_id)
        
        context = {
            'cliente': cliente,
        }
        
        return render(request, 'tauser/menu.html', context)
    
    except Cliente.DoesNotExist:
        request.session.flush()
        messages.error(request, 'Sesión inválida')
        return redirect('atm_login')
    
def atm_logout(request):
    """Cerrar sesión del ATM"""
    # Limpiar solo las variables de sesión del ATM
    request.session.pop('atm_cliente_id', None)
    request.session.pop('atm_cedula', None)
    request.session.pop('atm_nombre', None)
    
    messages.info(request, 'Sesión cerrada correctamente')
    return redirect('atm_login')


def atm_transacciones(request):
    """Vista para ver historial de transacciones del cliente"""
    cliente_id = request.session.get('atm_cliente_id')
    if not cliente_id:
        return redirect('atm_login')
    
    try:
        cliente = Cliente.objects.get(id=cliente_id)
        
        # Obtener todas las transacciones del cliente
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
        }
        
        return render(request, 'tauser/transacciones.html', context)
    
    except Cliente.DoesNotExist:
        request.session.flush()
        messages.error(request, 'Sesión inválida')
        return redirect('atm_login')

def atm_depositar(request):
    """
    Muestra las operaciones que requieren depósito en efectivo.
    Solo transacciones PENDIENTES pagadas en EFECTIVO.
    Después del depósito, actualiza el saldo del cliente considerando su segmentación.
    """
    cliente_id = request.session.get('atm_cliente_id')
    if not cliente_id:
        return redirect('atm_login')

    try:
        cliente = Cliente.objects.get(id=cliente_id)

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
                        moneda=moneda_deposito
                    )
                    
                except Exception as e:
                    print(f"Error al registrar depósito: {e}")
                    messages.error(request, f'Error al procesar el depósito: {str(e)}')
                    return redirect('atm_depositar')

                # ✅ ACTUALIZAR SALDO (solo si medio de acreditación es Tauser ID=0)
                es_tauser = transaccion.medio_acreditacion_id == 0
                
                if es_tauser:
                    from clientes.models import SaldoCliente
                    
                    # ✅ Usar el monto_recibir guardado en la transacción
                    moneda_recibir = transaccion.moneda_destino
                    monto_recibir = transaccion.monto_recibir if transaccion.monto_recibir else Decimal('0')
                    
                    # Obtener o crear el saldo
                    saldo, created = SaldoCliente.objects.get_or_create(
                        cliente=cliente,
                        moneda=moneda_recibir,
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
            'transacciones': transacciones_con_calculo,
        }
        return render(request, 'tauser/depositar.html', context)

    except Cliente.DoesNotExist:
        request.session.flush()
        messages.error(request, 'Sesión inválida')
        return redirect('atm_login')


def atm_extraer(request):
    """
    Vista para extraer dinero desde el saldo de Tauser.
    Permite retiro total automático o retiro parcial personalizado.
    """
    cliente_id = request.session.get('atm_cliente_id')
    if not cliente_id:
        return redirect('atm_login')
    
    try:
        cliente = Cliente.objects.get(id=cliente_id)
        
        # ✅ Obtener saldos del cliente en Tauser
        from clientes.models import SaldoCliente
        
        saldos_cliente = SaldoCliente.objects.filter(
            cliente=cliente,
            saldo__gt=0
        ).select_related('moneda').order_by('-saldo')
        
        monedas_con_detalle = []
        
        for saldo_obj in saldos_cliente:
            moneda = saldo_obj.moneda
            saldo_disponible = saldo_obj.saldo
            
            # ✅ Obtener stock de billetes disponibles en el ATM
            stock_billetes = StockTauser.objects.filter(
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
                    moneda
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
                    stock = StockTauser.objects.select_related('denominacion').get(denominacion_id=denom_id)
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
                                stock = StockTauser.objects.get(denominacion_id=denom_id)
                                
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
                    moneda
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
                    stock = StockTauser.objects.get(denominacion_id=denom_id)
                    
                    if stock.cantidad < cantidad:
                        messages.error(request, f'Stock insuficiente de billetes de {stock.denominacion.valor}')
                        return redirect('atm_extraer')
                    
                    stock.cantidad -= cantidad
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
                    mensaje = f'✓ Retiro exitoso: {int(monto_entregado):,} {moneda.abreviacion}'
                    if saldo_obj.saldo > 0:
                        mensaje += f'. Saldo restante: {int(saldo_obj.saldo):,} {moneda.abreviacion}'
                else:
                    mensaje = f'✓ Retiro exitoso: {monto_entregado:,.2f} {moneda.abreviacion}'
                    if saldo_obj.saldo > 0:
                        mensaje += f'. Saldo restante: {float(saldo_obj.saldo):,.2f} {moneda.abreviacion}'
                
                messages.success(request, mensaje)
            
            return redirect('atm_extraer')
        
        context = {
            'cliente': cliente,
            'monedas': monedas_con_detalle,
        }
        
        return render(request, 'tauser/extraer.html', context)
    
    except Cliente.DoesNotExist:
        request.session.flush()
        messages.error(request, 'Sesión inválida')
        return redirect('atm_login')
