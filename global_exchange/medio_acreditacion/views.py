from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.urls import reverse
from .models import TipoEntidadFinanciera, MedioAcreditacion
from .forms import TipoEntidadFinancieraForm, MedioAcreditacionForm
from clientes.forms import ClienteForm

# Listar entidades financieras
def tipo_entidad_list(request):
    entidades = TipoEntidadFinanciera.objects.all().order_by('-estado')
    # Crear formulario vacío para el modal
    form = TipoEntidadFinancieraForm()
    return render(request, 'medio_acreditacion/tipo_entidad_list.html', {
        'entidades': entidades,
        'form': form
    })

# Crear entidad financiera
def tipo_entidad_create(request):
    if request.method == 'POST':
        form = TipoEntidadFinancieraForm(request.POST)
        if form.is_valid():
            entidad = form.save(commit=False)
            entidad.estado = True 
            entidad.save()
            messages.success(request, 'Entidad financiera creada correctamente.')
            return redirect('tipo_entidad_list')
        else:
            # Si hay errores, devolver JSON para el modal
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                errors = {}
                for field, error_list in form.errors.items():
                    errors[field] = [str(error) for error in error_list]
                return JsonResponse({'success': False, 'errors': errors}, status=400)
    else:
        form = TipoEntidadFinancieraForm()
    
    return render(request, 'medio_acreditacion/tipo_entidad_form.html', {'form': form})

# Vista para obtener detalles de una entidad (para edición)
def tipo_entidad_detail(request, pk):
    entidad = get_object_or_404(TipoEntidadFinanciera, pk=pk)
    data = {
        'nombre': entidad.nombre,
        'tipo': entidad.tipo,
        'modal_title': f'Editar Entidad: {entidad.nombre}'
    }
    return JsonResponse(data)

# Editar entidad financiera
def tipo_entidad_update(request, pk):
    entidad = get_object_or_404(TipoEntidadFinanciera, pk=pk)
    print("Entidad: ", entidad.estado, flush=True)
    if request.method == 'POST':
        form = TipoEntidadFinancieraForm(request.POST, instance=entidad)
        if form.is_valid():
            form.save()
            messages.success(request, 'Entidad financiera actualizada correctamente.')
            return redirect('tipo_entidad_list')
        else:
            # Si hay errores, devolver JSON para el modal
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                errors = {}
                for field, error_list in form.errors.items():
                    errors[field] = [str(error) for error in error_list]
                return JsonResponse({'success': False, 'errors': errors}, status=400)
    else:
        form = TipoEntidadFinancieraForm(instance=entidad)
    
    return render(request, 'medio_acreditacion/tipo_entidad_form.html', {'form': form, 'entidad': entidad})

# Activar/desactivar entidad financiera
def tipo_entidad_toggle(request, pk):
    entidad = get_object_or_404(TipoEntidadFinanciera, pk=pk)
    entidad.estado = not entidad.estado
    entidad.save()
    messages.success(request, f'Entidad {"activada" if entidad.estado else "desactivada"}.')
    return redirect('tipo_entidad_list')

# Listar medios de acreditación
def medio_acreditacion_list(request):
    from clientes.models import Cliente
    cliente_id = request.GET.get('cliente_id')
    cliente = None
    clientes = Cliente.objects.all()
    if cliente_id:
        cliente = Cliente.objects.filter(pk=cliente_id).first()
        medios = MedioAcreditacion.objects.select_related('cliente', 'entidad').filter(cliente_id=cliente_id)
    else:
        medios = MedioAcreditacion.objects.select_related('cliente', 'entidad').all()
    form = MedioAcreditacionForm()
    return render(request, 'medio_acreditacion/medio_acreditacion_list.html', {'medios': medios, 'form': form, 'cliente': cliente, 'clientes': clientes})

# Crear medio de acreditación
def medio_acreditacion_create(request):
    cliente_id = request.GET.get('cliente_id') or request.POST.get('cliente_id')
    cliente = None
    if cliente_id:
        from clientes.models import Cliente
        cliente = Cliente.objects.filter(pk=cliente_id).first()
    if request.method == 'POST':
        data = request.POST.copy()
        if cliente:
            data['cliente'] = cliente.id
        form = MedioAcreditacionForm(data)
        if form.is_valid():
            medio_acred = form.save(commit=False)
            medio_acred.estado = True
            medio_acred.save()
            messages.success(request, 'Medio de acreditación creado correctamente.')
            if cliente:
                return redirect(f"{reverse('medio_acreditacion_list')}?cliente_id={cliente.id}")
            return redirect('medio_acreditacion_list')
    else:
        form = MedioAcreditacionForm()
    return render(request, 'medio_acreditacion/medio_acreditacion_form.html', {'form': form, 'cliente': cliente})

# Editar medio de acreditación
def medio_acreditacion_update(request, pk):
    medio = get_object_or_404(MedioAcreditacion, pk=pk)
    cliente = medio.cliente
    if request.method == 'POST':
        data = request.POST.copy()
        if cliente:
            data['cliente'] = cliente.id
        form = MedioAcreditacionForm(data, instance=medio)
        print("Data: ", form, flush=True)
        if form.is_valid():
            medio_edit = form.save(commit=False)
            medio_edit.estado = medio.estado  
            medio_edit.save()
            messages.success(request, 'Medio de acreditación actualizado correctamente.')
            if cliente:
                return redirect(f"{reverse('medio_acreditacion_list')}?cliente_id={cliente.id}")
            return redirect('medio_acreditacion_list')
    else:
        form = MedioAcreditacionForm(instance=medio)
    return render(request, 'medio_acreditacion/medio_acreditacion_form.html', {'form': form, 'medio': medio})

# Activar/desactivar medio de acreditación
def medio_acreditacion_toggle(request, pk):
    medio = get_object_or_404(MedioAcreditacion, pk=pk)
    medio.estado = not medio.estado
    medio.save()
    messages.success(request, f'Medio {"activado" if medio.estado else "desactivado"}.')
    return redirect('medio_acreditacion_list')

def medio_acreditacion_detail(request, pk):
    medio = get_object_or_404(MedioAcreditacion, pk=pk)
    print("Medio: ", medio.moneda, flush=True)
    data = {
        'cliente': medio.cliente_id,
        'entidad': medio.entidad_id,
        'numero_cuenta': medio.numero_cuenta,
        'tipo_cuenta': medio.tipo_cuenta,
        'titular': medio.titular,
        'documento_titular': medio.documento_titular,
        'moneda': medio.moneda_id,
        'estado': bool(medio.estado),
        'modal_title': 'Editar Medio'
    }
    return JsonResponse(data)
# Crear cliente y medio de acreditación
def cliente_create(request):
    if request.method == 'POST':
        cliente_form = ClienteForm(request.POST)
        medio_form = MedioAcreditacionForm(request.POST)
        if cliente_form.is_valid() and medio_form.is_valid():
            cliente = cliente_form.save()
            medio = medio_form.save(commit=False)
            medio.cliente = cliente
            medio.save()
            messages.success(request, 'Cliente y medio de acreditación creados correctamente.')
            return redirect('clientes_list')
    else:
        cliente_form = ClienteForm()
        medio_form = MedioAcreditacionForm()
    return render(request, 'clientes/form.html', {
        'form': cliente_form,
        'medio_form': medio_form,
    })