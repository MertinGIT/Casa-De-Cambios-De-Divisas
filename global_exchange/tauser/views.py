from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction as db_transaction
from django.db.models import Sum, Q
from clientes.models import Cliente
from operaciones.models import Transaccion
from .forms import LoginATMForm, SeleccionarTransaccionForm
from tauser.models import StockTauser
from tauser.utils import GestorStockTauser

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
    """
    cliente_id = request.session.get('atm_cliente_id')
    if not cliente_id:
        return redirect('atm_login')

    try:
        cliente = Cliente.objects.get(id=cliente_id)

        # Buscar transacciones pendientes en efectivo
        transacciones_pendientes = Transaccion.objects.filter(
            cliente=cliente,
            estado='pendiente',
            metodo_pago__nombre__iexact='efectivo'
        ).select_related('moneda_origen', 'moneda_destino', 'metodo_pago').order_by('-fecha')

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
                GestorStockTauser.registrar_deposito(transaccion)
                transaccion.estado = 'confirmada'
                transaccion.save(update_fields=['estado'])

            # ✅ Guardar el ID en la sesión para usarlo en el modal
            request.session['ultima_transaccion_id'] = transaccion_id

            messages.success(
                request,
                f'✓ Depósito exitoso: {transaccion.monto:.2f} {transaccion.moneda_origen.abreviacion}'
            )
            return redirect('atm_depositar')

        context = {
            'cliente': cliente,
            'transacciones': transacciones_pendientes,
            # ✅ Pasar el ID de la última transacción si existe
            'ultima_transaccion_id': request.session.pop('ultima_transaccion_id', None)
        }
        return render(request, 'tauser/depositar.html', context)

    except Cliente.DoesNotExist:
        request.session.flush()
        messages.error(request, 'Sesión inválida')
        return redirect('atm_login')


def atm_extraer(request):
    """
    Vista para extraer dinero.
    EXTRAER = Cliente COMPRA divisas (tipo='compra')
    Muestra transacciones de COMPRA pendientes agrupadas por moneda
    """
    cliente_id = request.session.get('atm_cliente_id')
    if not cliente_id:
        return redirect('atm_login')
    
    try:
        cliente = Cliente.objects.get(id=cliente_id)
        
        # Obtener transacciones de COMPRA pendientes
        transacciones_pendientes = Transaccion.objects.filter(
            cliente=cliente,
            tipo='compra',
            estado='confirmada'
        ).select_related('moneda_origen', 'moneda_destino').order_by('-fecha')
        
        # Agrupar por moneda destino
        monedas_agrupadas = {}
        
        for trans in transacciones_pendientes:
            moneda_destino = trans.moneda_destino
            monto_retirar = trans.monto / trans.tasa_usada
            
            # Inicializar moneda si no existe
            if moneda_destino.id not in monedas_agrupadas:
                monedas_agrupadas[moneda_destino.id] = {
                    'moneda': moneda_destino,
                    'total_disponible': 0,
                    'transacciones': []
                }
            
            # Acumular total
            monedas_agrupadas[moneda_destino.id]['total_disponible'] += monto_retirar
            
            # Agregar transacción con sus detalles
            monedas_agrupadas[moneda_destino.id]['transacciones'].append({
                'transaccion': trans,
                'monto_retirar': monto_retirar
            })
        
        # Calcular billetes disponibles para cada moneda
        monedas_con_detalle = []
        for moneda_data in monedas_agrupadas.values():
            total = moneda_data['total_disponible']
            moneda = moneda_data['moneda']
            
            # Calcular billetes óptimos para el total
            billetes, monto_entregado, diferencia, posible = GestorStockTauser.calcular_billetes_optimo(
                total, 
                moneda
            )
            
            # Obtener detalles de billetes
            detalles_billetes = []
            for denom_id, cantidad in billetes.items():
                stock = StockTauser.objects.select_related('denominacion').get(denominacion_id=denom_id)
                detalles_billetes.append({
                    'denominacion': stock.denominacion,
                    'cantidad': cantidad,
                    'subtotal': stock.denominacion.valor / cantidad
                })
            
            monedas_con_detalle.append({
                'moneda': moneda,
                'total_disponible': total,
                'monto_entregado': monto_entregado,
                'diferencia': diferencia,
                'posible_efectivo': posible,
                'billetes': detalles_billetes,
                'transacciones': moneda_data['transacciones'],
                'cantidad_transacciones': len(moneda_data['transacciones'])
            })
        
        if request.method == 'POST':
            moneda_id = request.POST.get('moneda_id')
            
            if not moneda_id:
                messages.error(request, 'Datos incompletos')
                return redirect('atm_extraer')
            
            # Obtener todas las transacciones de esa moneda
            transacciones_moneda = Transaccion.objects.filter(
                cliente=cliente,
                tipo='compra',
                estado='confirmada',
                moneda_destino_id=moneda_id
            )
            
            if not transacciones_moneda.exists():
                messages.error(request, 'No hay transacciones para esta moneda')
                return redirect('atm_extraer')
            
            # Calcular monto total
            monto_total = sum(t.monto / t.tasa_usada for t in transacciones_moneda)
            moneda = transacciones_moneda.first().moneda_destino
            
            with db_transaction.atomic():
                # Calcular billetes disponibles
                billetes, monto_entregado, diferencia, posible = GestorStockTauser.calcular_billetes_optimo(
                    monto_total,
                    moneda
                )
                
                if monto_entregado == 0:
                    messages.error(
                        request,
                        f'No hay billetes disponibles para entregar. Intenta más tarde.'
                    )
                    return redirect('atm_extraer')
                
                # Actualizar stock de billetes
                for denom_id, cantidad in billetes.items():
                    stock = StockTauser.objects.get(denominacion_id=denom_id)
                    stock.cantidad -= cantidad
                    stock.save()
                
                # Calcular cuánto se retira de cada transacción proporcionalmente
                monto_restante_entregar = monto_entregado
                
                for transaccion in transacciones_moneda:
                    monto_transaccion = transaccion.monto / transaccion.tasa_usada
                    
                    if monto_restante_entregar >= monto_transaccion:
                        # Se puede retirar completa
                        transaccion.estado = 'confirmada'
                        monto_restante_entregar -= monto_transaccion
                    else:
                        # Se retira parcial, queda pendiente
                        if monto_restante_entregar > 0:
                            # Crear nueva transacción por lo retirado
                            proporcion_retirada = monto_restante_entregar / monto_transaccion
                            
                            # Actualizar la transacción original (reducir monto)
                            transaccion.monto = transaccion.monto * (1 - proporcion_retirada)
                            transaccion.save()
                            
                            monto_restante_entregar = 0
                        # Si ya no queda nada por entregar, esta transacción queda pendiente completa
                    
                    transaccion.save()
                
                if diferencia > 0:
                    messages.success(
                        request,
                        f'✓ Retiro confirmado: {monto_entregado:.2f} {moneda.abreviacion}. '
                        f'Quedó pendiente: {diferencia:.2f} {moneda.abreviacion} (disponible para próximo retiro)'
                    )
                else:
                    messages.success(
                        request,
                        f'✓ Retiro completo confirmado: {monto_entregado:.2f} {moneda.abreviacion}'
                    )
            
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
