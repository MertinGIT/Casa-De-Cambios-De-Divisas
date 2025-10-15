from django.shortcuts import render, redirect
from django.contrib import messages
from clientes.models import Cliente
from operaciones.models import Transaccion
from .forms import LoginATMForm


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
    """Vista para depositar dinero (sin lógica por ahora)"""
    cliente_id = request.session.get('atm_cliente_id')
    if not cliente_id:
        return redirect('atm_login')
    
    try:
        cliente = Cliente.objects.get(id=cliente_id)
        
        context = {
            'cliente': cliente,
        }
        
        return render(request, 'tauser/depositar.html', context)
    
    except Cliente.DoesNotExist:
        request.session.flush()
        messages.error(request, 'Sesión inválida')
        return redirect('atm_login')


def atm_extraer(request):
    """Vista para extraer dinero (sin lógica por ahora)"""
    cliente_id = request.session.get('atm_cliente_id')
    if not cliente_id:
        return redirect('atm_login')
    
    try:
        cliente = Cliente.objects.get(id=cliente_id)
        
        context = {
            'cliente': cliente,
        }
        
        return render(request, 'tauser/extraer.html', context)
    
    except Cliente.DoesNotExist:
        request.session.flush()
        messages.error(request, 'Sesión inválida')
        return redirect('atm_login')
