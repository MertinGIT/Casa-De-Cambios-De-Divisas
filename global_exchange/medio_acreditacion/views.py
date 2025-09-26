from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.urls import reverse
from django.core.paginator import Paginator
from .models import TipoEntidadFinanciera, MedioAcreditacion
from .forms import TipoEntidadFinancieraForm, MedioAcreditacionForm
from clientes.forms import ClienteForm

def tipo_entidad_list(request):
    """
    Lista todas las entidades financieras con paginación y búsqueda por nombre y tipo.

    Renderiza la plantilla `tipo_entidad_list.html` con todas las entidades y un formulario vacío
    para el modal de creación.

    :param request: HttpRequest
    :return: HttpResponse
    """
    search_nombre = request.GET.get('search_nombre', '').strip()
    search_tipo = request.GET.get('search_tipo', '').strip()
    entidades_qs = TipoEntidadFinanciera.objects.all().order_by('-estado')
    if search_nombre:
        entidades_qs = entidades_qs.filter(nombre__icontains=search_nombre)
    if search_tipo:
        entidades_qs = entidades_qs.filter(tipo__icontains=search_tipo)
    paginator = Paginator(entidades_qs, 10)  # 10 por página
    page_number = request.GET.get('page')
    entidades = paginator.get_page(page_number)
    form = TipoEntidadFinancieraForm()
    tipos = TipoEntidadFinanciera._meta.get_field('tipo').choices
    # Para compatibilidad con paginador estilo clientes
    page_obj = entidades
    return render(request, 'medio_acreditacion/tipo_entidad_list.html', {
        'entidades': entidades,
        'form': form,
        'search_nombre': search_nombre,
        'search_tipo': search_tipo,
        'tipos': tipos,
        'page_obj': page_obj,
        'request': request,
    })

def tipo_entidad_create(request):
    """
    Crea una nueva entidad financiera.

    - Si la solicitud es POST y el formulario es válido, guarda la entidad y redirige a la lista.
    - Si el formulario no es válido y es una solicitud AJAX, devuelve errores en JSON.
    - Si la solicitud no es POST, renderiza el formulario vacío.

    :param request: HttpRequest
    :return: HttpResponse o JsonResponse
    """
    if request.method == 'POST':
        form = TipoEntidadFinancieraForm(request.POST)
        if form.is_valid():
            entidad = form.save(commit=False)
            entidad.estado = True 
            entidad.save()
            messages.success(request, 'Entidad financiera creada correctamente.')
            return redirect('tipo_entidad_list')
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                errors = {}
                for field, error_list in form.errors.items():
                    errors[field] = [str(error) for error in error_list]
                return JsonResponse({'success': False, 'errors': errors}, status=400)
    else:
        form = TipoEntidadFinancieraForm()
    
    return render(request, 'medio_acreditacion/tipo_entidad_form.html', {'form': form})

def tipo_entidad_detail(request, pk):
    """
    Obtiene los detalles de una entidad financiera para edición.

    Devuelve un JsonResponse con los datos de la entidad y un título para el modal de edición.

    :param request: HttpRequest
    :param pk: Primary key de la entidad
    :return: JsonResponse
    """
    entidad = get_object_or_404(TipoEntidadFinanciera, pk=pk)
    data = {
        'nombre': entidad.nombre,
        'tipo': entidad.tipo,
        'modal_title': f'Editar Entidad: {entidad.nombre}'
    }
    return JsonResponse(data)

def tipo_entidad_update(request, pk):
    """
    Edita una entidad financiera existente.

    - Si POST y el formulario es válido, actualiza la entidad y redirige a la lista.
    - Si el formulario no es válido y es AJAX, devuelve errores en JSON.
    - Si no es POST, renderiza el formulario con los datos actuales.

    :param request: HttpRequest
    :param pk: Primary key de la entidad
    :return: HttpResponse o JsonResponse
    """
    entidad = get_object_or_404(TipoEntidadFinanciera, pk=pk)
    print("Entidad: ", entidad.estado, flush=True)
    if request.method == 'POST':
        form = TipoEntidadFinancieraForm(request.POST, instance=entidad)
        if form.is_valid():
            form.save()
            messages.success(request, 'Entidad financiera actualizada correctamente.')
            return redirect('tipo_entidad_list')
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                errors = {}
                for field, error_list in form.errors.items():
                    errors[field] = [str(error) for error in error_list]
                return JsonResponse({'success': False, 'errors': errors}, status=400)
    else:
        form = TipoEntidadFinancieraForm(instance=entidad)
    
    return render(request, 'medio_acreditacion/tipo_entidad_form.html', {'form': form, 'entidad': entidad})

def tipo_entidad_toggle(request, pk):
    """
    Activa o desactiva una entidad financiera.

    Cambia el estado de la entidad y muestra un mensaje de éxito.

    :param request: HttpRequest
    :param pk: Primary key de la entidad
    :return: HttpResponseRedirect a la lista de entidades
    """
    entidad = get_object_or_404(TipoEntidadFinanciera, pk=pk)
    entidad.estado = not entidad.estado
    entidad.save()
    messages.success(request, f'Entidad {"activada" if entidad.estado else "desactivada"}.')
    return redirect('tipo_entidad_list')

def medio_acreditacion_list(request):
    """
    Lista todos los medios de acreditación, opcionalmente filtrando por cliente, y permite búsqueda y paginación.

    Renderiza la plantilla `medio_acreditacion_list.html` con los medios, clientes y formulario.

    :param request: HttpRequest
    :return: HttpResponse
    """
    from clientes.models import Cliente
    cliente_id = request.GET.get('cliente_id')
    search_field = request.GET.get('search_field', '').strip()
    search_value = request.GET.get('search_value', '').strip()
    cliente = None
    clientes = Cliente.objects.all()
    medios_qs = MedioAcreditacion.objects.select_related('cliente', 'entidad', 'moneda').all()
    if cliente_id:
        cliente = Cliente.objects.filter(pk=cliente_id).first()
        medios_qs = medios_qs.filter(cliente_id=cliente_id)
    # Buscador por campo
    if search_field and search_value:
        if search_field == 'titular':
            medios_qs = medios_qs.filter(titular__icontains=search_value)
        elif search_field == 'entidad':
            medios_qs = medios_qs.filter(entidad__nombre__icontains=search_value)
        elif search_field == 'numero_cuenta':
            medios_qs = medios_qs.filter(numero_cuenta__icontains=search_value)
        elif search_field == 'tipo_cuenta':
            medios_qs = medios_qs.filter(tipo_cuenta__icontains=search_value)
        elif search_field == 'moneda':
            medios_qs = medios_qs.filter(moneda__nombre__icontains=search_value)
    medios_qs = medios_qs.order_by('-estado', 'titular')
    paginator = Paginator(medios_qs, 10)  # 10 por página
    page_number = request.GET.get('page')
    medios = paginator.get_page(page_number)
    form = MedioAcreditacionForm()
    # Para compatibilidad con paginador estilo clientes
    page_obj = medios
    # Campos disponibles para búsqueda
    search_fields = [
        ('titular', 'Titular'),
        ('entidad', 'Entidad'),
        ('numero_cuenta', 'Número de Cuenta'),
        ('tipo_cuenta', 'Tipo de Cuenta'),
        ('moneda', 'Moneda'),
    ]
    return render(request, 'medio_acreditacion/medio_acreditacion_list.html', {
        'medios': medios,
        'form': form,
        'cliente': cliente,
        'clientes': clientes,
        'search_field': search_field,
        'search_value': search_value,
        'search_fields': search_fields,
        'page_obj': page_obj,
        'request': request,
    })

def medio_acreditacion_create(request):
    """
    Crea un nuevo medio de acreditación.

    - Asocia el medio al cliente si se proporciona `cliente_id`.
    - Muestra mensajes de éxito y redirige a la lista correspondiente.

    :param request: HttpRequest
    :return: HttpResponse
    """
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

def medio_acreditacion_update(request, pk):
    """
    Edita un medio de acreditación existente.

    - Mantiene el estado original del medio.
    - Redirige a la lista filtrada por cliente si corresponde.
    - Renderiza el formulario con datos actuales si no es POST.

    :param request: HttpRequest
    :param pk: Primary key del medio de acreditación
    :return: HttpResponse
    """
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

def medio_acreditacion_toggle(request, pk):
    """
    Activa o desactiva un medio de acreditación.

    - Cambia el estado del medio.
    - Redirige a la lista de medios, filtrada por cliente si aplica.

    :param request: HttpRequest
    :param pk: Primary key del medio
    :return: HttpResponseRedirect
    """
    medio = get_object_or_404(MedioAcreditacion, pk=pk)
    medio.estado = not medio.estado
    medio.save()
    messages.success(request, f'Medio {"activado" if medio.estado else "desactivado"}.')
    cliente_id = request.GET.get('cliente_id') or medio.cliente_id
    if cliente_id:
        from django.urls import reverse
        return redirect(f"{reverse('medio_acreditacion_list')}?cliente_id={cliente_id}")
    return redirect('medio_acreditacion_list')

def medio_acreditacion_detail(request, pk):
    """
    Obtiene los detalles de un medio de acreditación para edición.

    Devuelve un JsonResponse con los datos del medio y título para modal.

    :param request: HttpRequest
    :param pk: Primary key del medio
    :return: JsonResponse
    """
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

def cliente_create(request):
    """
    Crea un nuevo cliente y su medio de acreditación asociado.

    - Valida ambos formularios antes de guardar.
    - Muestra mensajes de éxito y redirige a la lista de clientes.
    - Si no es POST, renderiza formularios vacíos.

    :param request: HttpRequest
    :return: HttpResponse
    """
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