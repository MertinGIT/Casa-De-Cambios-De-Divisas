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
    Muestra las operaciones que requieren depósito en efectivo (ventas y compras pagadas en efectivo).
    """
    cliente_id = request.session.get('atm_cliente_id')
    if not cliente_id:
        return redirect('atm_login')

    try:
        cliente = Cliente.objects.get(id=cliente_id)

        # 1️⃣ Total ya depositado (solo confirmadas)
        total_confirmadas = Transaccion.objects.filter(
            cliente=cliente,
            estado='confirmada'
        ).aggregate(total=Sum('monto'))['total'] or 0

        # 2️⃣ Transacciones pendientes que requieren depósito (ventas o compras pagadas en efectivo)
        transacciones_pendientes = Transaccion.objects.filter(
            cliente=cliente,
            estado='pendiente',
            metodo_pago_id=3,  # efectivo
        ).select_related('moneda_origen', 'moneda_destino').order_by('-fecha')

        if request.method == 'POST':
            form = SeleccionarTransaccionForm(request.POST)
            if form.is_valid():
                transaccion_id = form.cleaned_data['transaccion_id']
                transaccion = get_object_or_404(
                    Transaccion,
                    id=transaccion_id,
                    cliente=cliente,
                    estado='pendiente',
                    metodo_pago_id=3
                )

                with db_transaction.atomic():
                    
                    GestorStockTauser.registrar_deposito(transaccion)

                    transaccion.estado = 'completada'
                    transaccion.save(update_fields=['estado'])


                messages.success(
                    request,
                    f'Depósito confirmado: {transaccion.monto} {transaccion.moneda_origen.codigo}'
                )
                return redirect('atm_dashboard')
        else:
            form = SeleccionarTransaccionForm()

        context = {
            'cliente': cliente,
            'transacciones': transacciones_pendientes,
            'total_confirmadas': total_confirmadas,
            'form': form,
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
    Muestra transacciones de COMPRA pendientes y permite retirar en efectivo o transferencia
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
            estado='completada'
        ).select_related('moneda_origen', 'moneda_destino').order_by('-fecha')
        
        # Calcular disponibilidad de billetes para cada transacción
        transacciones_con_detalle = []
        for trans in transacciones_pendientes:
            # El monto a retirar es en moneda_destino (la que compró)
            monto_retirar = trans.monto * trans.tasa_usada
            moneda_retirar = trans.moneda_destino
            
            # Calcular billetes óptimos
            billetes, monto_entregado, diferencia, posible = GestorStockTauser.calcular_billetes_optimo(
                monto_retirar, 
                moneda_retirar
            )
            
            # Obtener detalles de billetes
            detalles_billetes = []
            for denom_id, cantidad in billetes.items():
                stock = StockTauser.objects.select_related('denominacion').get(denominacion_id=denom_id)
                detalles_billetes.append({
                    'denominacion': stock.denominacion,
                    'cantidad': cantidad,
                    'subtotal': stock.denominacion.valor * cantidad
                })
            
            transacciones_con_detalle.append({
                'transaccion': trans,
                'monto_retirar': monto_retirar,
                'monto_entregado': monto_entregado,
                'diferencia': diferencia,
                'posible_efectivo': posible,
                'billetes': detalles_billetes
            })
        
        if request.method == 'POST':
            form = SeleccionarTransaccionForm(request.POST)
            if form.is_valid():
                transaccion_id = form.cleaned_data['transaccion_id']
                metodo_pago = form.cleaned_data['metodo_pago']
                
                transaccion = get_object_or_404(
                    Transaccion,
                    id=transaccion_id,
                    cliente=cliente,
                    tipo='compra',
                    estado='pendiente'
                )
                
                monto_retirar = transaccion.monto * transaccion.tasa_usada
                moneda_retirar = transaccion.moneda_destino
                
                with db_transaction.atomic():
                    if metodo_pago == 'efectivo':
                        # Verificar disponibilidad de billetes
                        billetes, monto_entregado, diferencia, posible = GestorStockTauser.calcular_billetes_optimo(
                            monto_retirar,
                            moneda_retirar
                        )
                        
                        if not posible:
                            messages.warning(
                                request,
                                f'No se puede entregar el monto completo. '
                                f'Se puede entregar: {monto_entregado} {moneda_retirar.codigo}. '
                                f'Diferencia: {diferencia} {moneda_retirar.codigo}'
                            )
                            # Aquí podrías preguntar si acepta el monto parcial o prefiere transferencia
                            return redirect('atm_extraer')
                        
                        # Registrar el retiro y actualizar stock
                        GestorStockTauser.registrar_retiro(
                            transaccion,
                            billetes,
                            monto_retirar,
                            monto_entregado,
                            diferencia
                        )
                        
                        transaccion.estado = 'confirmada'
                        transaccion.save()
                        
                        messages.success(
                            request,
                            f'Retiro en efectivo confirmado: {monto_entregado} {moneda_retirar.codigo}'
                        )
                    
                    elif metodo_pago == 'transferencia':
                        # Para transferencia no necesita stock físico
                        transaccion.estado = 'confirmada'
                        transaccion.save()
                        
                        messages.success(
                            request,
                            f'Retiro por transferencia confirmado: {monto_retirar} {moneda_retirar.codigo}'
                        )
                
                return redirect('atm_dashboard')
        else:
            form = SeleccionarTransaccionForm()
        
        context = {
            'cliente': cliente,
            'transacciones': transacciones_con_detalle,
            'form': form,
        }
        
        return render(request, 'tauser/extraer.html', context)
    
    except Cliente.DoesNotExist:
        request.session.flush()
        messages.error(request, 'Sesión inválida')
        return redirect('atm_login')


