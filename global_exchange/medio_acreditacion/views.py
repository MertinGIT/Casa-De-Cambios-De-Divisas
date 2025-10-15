from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.urls import reverse
from django.db.models import Count
from django.core.paginator import Paginator
from .models import TipoEntidadFinanciera, MedioAcreditacion, CampoEntidadFinanciera, ValorCampoMedioAcreditacion
from .forms import TipoEntidadFinancieraForm, MedioAcreditacionForm
from clientes.forms import ClienteForm
from clientes.models import Cliente
from monedas.models import Moneda
from django.template.loader import render_to_string
from operaciones.views import obtener_clientes_usuario

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
        'comision': float(entidad.comision),
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
    return redirect('tipo_entidad_list')

def medio_acreditacion_list(request):
    """
    Lista todos los medios de acreditación, filtrando únicamente por cliente_operativo global.
    Renderiza la plantilla `medio_acreditacion_list.html` con los medios, clientes y formulario.
    """
    cliente = None
    # Obtener cliente operativo asociado al usuario autenticado
    cliente_operativo = None
    clientes_asociados = None
    segmento_nombre = None
    descuento = None
    if request.user.is_authenticated:
        clientes_asociados, cliente_operativo, _ = obtener_clientes_usuario(request.user, request)
    # Filtrar solo por cliente_operativo
    if cliente_operativo:
        cliente = cliente_operativo
    medios_qs = MedioAcreditacion.objects.select_related('cliente', 'entidad').all()
    if cliente:
        medios_qs = medios_qs.filter(cliente_id=cliente.id)
    if cliente_operativo and cliente_operativo.segmentacion and cliente_operativo.segmentacion.estado == "activo":
        descuento = float(cliente_operativo.segmentacion.descuento or 0)
        segmento_nombre = cliente_operativo.segmentacion.nombre
    # Si no hay cliente seleccionado, mostrar advertencia y no permitir agregar medios
    cliente_context_required = False
    if not cliente:
        cliente_context_required = True
    # Eliminar buscador por campo cliente y cualquier filtro manual
    medios_qs = medios_qs.order_by('-estado', 'entidad__nombre')
    paginator = Paginator(medios_qs, 10)  # 10 por página
    page_number = request.GET.get('page')
    medios = paginator.get_page(page_number)
    form = MedioAcreditacionForm()
    page_obj = medios
    search_fields = [
        ('entidad', 'Entidad'),
        ('estado', 'Estado'),
    ]
    entidades = TipoEntidadFinanciera.objects.filter(estado=True).annotate(num_campos=Count('campos')).filter(num_campos__gt=0)
    print(f"ENTIDADES: {entidades}", flush=True)
    return render(request, 'medio_acreditacion/medio_acreditacion_list.html', {
        'medios': medios,
        'form': form,
        'user': request.user,
        'cliente': cliente,
        'clientes': clientes_asociados,
        'search_fields': search_fields,
        'page_obj': page_obj,
        'request': request,
        'entidades': entidades,
        'cliente_context_required': cliente_context_required,
        'clientes_asociados': clientes_asociados,
        "cliente_operativo": cliente_operativo,        
        "segmento": segmento_nombre,
        "descuento": descuento,
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
    data = {
        'cliente': medio.cliente_id,
        'entidad': medio.entidad_id,
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
            return redirect('clientes_list')
    else:
        cliente_form = ClienteForm()
        medio_form = MedioAcreditacionForm()
    return render(request, 'clientes/form.html', {
        'form': cliente_form,
        'medio_form': medio_form,
    })

# Vista para que el analista gestione los campos de una entidad financiera

def campos_entidad_list(request, entidad_id):
    """
    Muestra y permite agregar campos personalizados a una entidad financiera.

    Esta vista lista todos los `CampoEntidadFinanciera` asociados a una entidad y,
    en caso de recibir una solicitud POST, crea un nuevo campo con los datos enviados.

    :param request: Objeto HttpRequest que contiene la información de la solicitud.
    :param entidad_id: ID de la entidad financiera (TipoEntidadFinanciera) cuyos campos se gestionan.
    :return: Renderiza la plantilla HTML correspondiente o redirige tras la creación exitosa.
    """
    entidad = get_object_or_404(TipoEntidadFinanciera, pk=entidad_id)
    campos = entidad.campos.all().order_by('orden')
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        etiqueta = request.POST.get('etiqueta')
        tipo = request.POST.get('tipo')
        requerido = bool(request.POST.get('requerido'))
        orden = int(request.POST.get('orden', 0))
        CampoEntidadFinanciera.objects.create(
            entidad=entidad, nombre=nombre, etiqueta=etiqueta, tipo=tipo, requerido=requerido, orden=orden
        )
        messages.success(request, "Campo agregado correctamente.")
        return redirect('campos_entidad_list', entidad_id=entidad.id)
    return render(request, 'medio_acreditacion/campos_entidad_list.html', {
        'entidad': entidad,
        'campos': campos,
    })

# Vista para mostrar y guardar formulario dinámico de medio de acreditación (solo creación)
def medio_acreditacion_dinamico(request, entidad_id, cliente_id):
    """
    Genera, valida y guarda formularios dinámicos de medios de acreditación.

    Dependiendo del método HTTP:
      - GET: Renderiza el formulario con los campos definidos por la entidad.
      - POST: Valida los datos ingresados, guarda o actualiza los valores dinámicos
        asociados al `MedioAcreditacion`.

    :param request: Objeto HttpRequest con la solicitud del usuario.
    :param entidad_id: ID de la entidad financiera asociada.
    :param cliente_id: ID del cliente que está registrando el medio.
    :return: JsonResponse con el resultado de la operación (success, html).
    """
    from django.db import transaction
    entidad = get_object_or_404(TipoEntidadFinanciera, pk=entidad_id)
    cliente = get_object_or_404(Cliente, pk=cliente_id)
    campos = entidad.campos.order_by('orden')
    monedas = Moneda.objects.filter(estado=True)
    errores = {}
    valores = {}
    medio_id = request.GET.get('medio_id') or request.POST.get('medio_id')
    medio = None
    if medio_id:
        medio = MedioAcreditacion.objects.filter(pk=medio_id, entidad=entidad, cliente=cliente).first()
        # Cargar valores actuales si existe
        if medio:
            valores = {v.campo_id: v.valor for v in ValorCampoMedioAcreditacion.objects.filter(medio=medio)}
    if request.method == 'POST':
        # Validate and collect values
        for campo in campos:
            field_name = f"campo_{campo.id}"
            valor = request.POST.get(field_name, '').strip()
            valores[campo.id] = valor
            if campo.requerido and not valor:
                errores[campo.id] = 'Este campo es obligatorio.'
            elif campo.regex_validacion and valor:
                import re
                if not re.match(campo.regex_validacion, valor):
                    errores[campo.id] = campo.mensaje_error or 'Formato inválido.'
        if errores:
            html = render_to_string('medio_acreditacion/medio_acreditacion_dinamico.html', {
                'entidad': entidad,
                'campos': campos,
                'cliente': cliente,
                'errores': errores,
                'valores': valores,
                'monedas': monedas,
                'medio': medio,
            }, request=request)
            return JsonResponse({'success': False, 'html': html})
        # Crear o actualizar MedioAcreditacion
        with transaction.atomic():
            if medio:
                # Actualizar valores dinámicos existentes
                for campo in campos:
                    vcm = ValorCampoMedioAcreditacion.objects.filter(medio=medio, campo=campo).first()
                    if vcm:
                        vcm.valor = valores.get(campo.id, '')
                        vcm.save()
                    else:
                        ValorCampoMedioAcreditacion.objects.create(medio=medio, campo=campo, valor=valores.get(campo.id, ''))
            else:
                medio = MedioAcreditacion.objects.create(
                    cliente=cliente,
                    entidad=entidad,
                    estado=True
                )
                for campo in campos:
                    ValorCampoMedioAcreditacion.objects.create(
                        medio=medio,
                        campo=campo,
                        valor=valores.get(campo.id, '')
                    )
        html = '<div class="success-message">Medio de acreditación guardado correctamente.</div>'
        return JsonResponse({'success': True, 'html': html})
    # GET: retornar formulario vacío o con valores actuales
    html = render_to_string('medio_acreditacion/medio_acreditacion_dinamico.html', {
        'entidad': entidad,
        'campos': campos,
        'cliente': cliente,
        'errores': errores,
        'valores': valores,
        'monedas': monedas,
        'medio': medio,
    }, request=request)
    return JsonResponse({'success': False, 'html': html})

def campo_entidad_create(request, entidad_id):
    """
    Crea un nuevo campo personalizado para una entidad financiera.

    Realiza validaciones de duplicidad y formato antes de registrar el campo.
    Soporta solicitudes AJAX (retornando HTML parcial) y normales (con redirección).

    :param request: Objeto HttpRequest.
    :param entidad_id: ID de la entidad (TipoEntidadFinanciera).
    :return: JsonResponse o render con el formulario actualizado.
    """
    entidad = get_object_or_404(TipoEntidadFinanciera, pk=entidad_id)
    
    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        etiqueta = request.POST.get('etiqueta', '').strip()
        tipo = request.POST.get('tipo', '').strip()
        requerido = bool(request.POST.get('requerido'))
        orden = int(request.POST.get('orden', 0))
        regex_validacion = request.POST.get('regex_validacion', '').strip()
        mensaje_error = request.POST.get('mensaje_error', '').strip()
        placeholder = request.POST.get('placeholder', '').strip()
        ayuda = request.POST.get('ayuda', '').strip()
        
        # Validación
        errores = {}
        if not nombre:
            errores['nombre'] = 'El nombre interno es obligatorio.'
        if not etiqueta:
            errores['etiqueta'] = 'La etiqueta visible es obligatoria.'
        if not tipo:
            errores['tipo'] = 'El tipo de campo es obligatorio.'
        
        # Verificar que el nombre no exista ya para esta entidad
        if nombre and CampoEntidadFinanciera.objects.filter(entidad=entidad, nombre=nombre).exists():
            errores['nombre'] = 'Ya existe un campo con este nombre para esta entidad.'
        
        if errores:
            campo = CampoEntidadFinanciera(
                entidad=entidad, nombre=nombre, etiqueta=etiqueta, tipo=tipo, 
                requerido=requerido, orden=orden, regex_validacion=regex_validacion, 
                mensaje_error=mensaje_error, placeholder=placeholder, ayuda=ayuda
            )
            html = render_to_string('medio_acreditacion/campo_entidad_form.html', 
                                  {'entidad': entidad, 'campo': campo, 'errores': errores}, 
                                  request=request)
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'html': html})
            return render(request, 'medio_acreditacion/campo_entidad_form.html', 
                        {'entidad': entidad, 'campo': campo, 'errores': errores})
        
        # Crear el campo
        campo = CampoEntidadFinanciera.objects.create(
            entidad=entidad, nombre=nombre, etiqueta=etiqueta, tipo=tipo, 
            requerido=requerido, orden=orden, regex_validacion=regex_validacion, 
            mensaje_error=mensaje_error, placeholder=placeholder, ayuda=ayuda
        )
        
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            campos = entidad.campos.all().order_by('orden')
            html = render_to_string('medio_acreditacion/partials/campos_entidad_table.html', 
                                  {'campos': campos, 'entidad': entidad}, 
                                  request=request)
            return JsonResponse({'success': True, 'html': html})
        
        messages.success(request, 'Campo agregado correctamente.')
        return redirect('campos_entidad_list', entidad_id=entidad.id)
    
    # GET request
    html = render_to_string('medio_acreditacion/campo_entidad_form.html', 
                          {'entidad': entidad, 'campo': None, 'errores': {}}, 
                          request=request)
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'success': False, 'html': html})
    return render(request, 'medio_acreditacion/campo_entidad_form.html', 
                {'entidad': entidad, 'campo': None, 'errores': {}})


def campo_entidad_edit(request, campo_id):
    """
    Edita los datos de un campo personalizado existente.

    Permite modificar los atributos del campo y realiza validaciones
    de duplicidad y consistencia. Admite solicitudes AJAX y normales.

    :param request: Objeto HttpRequest.
    :param campo_id: ID del campo (CampoEntidadFinanciera) a editar.
    :return: JsonResponse o render actualizado según el tipo de solicitud.
    """
    campo = get_object_or_404(CampoEntidadFinanciera, pk=campo_id)
    entidad = campo.entidad
    
    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        etiqueta = request.POST.get('etiqueta', '').strip()
        tipo = request.POST.get('tipo', '').strip()
        requerido = bool(request.POST.get('requerido'))
        orden = int(request.POST.get('orden', 0))
        regex_validacion = request.POST.get('regex_validacion', '').strip()
        mensaje_error = request.POST.get('mensaje_error', '').strip()
        placeholder = request.POST.get('placeholder', '').strip()
        ayuda = request.POST.get('ayuda', '').strip()
        
        # Validación
        errores = {}
        if not nombre:
            errores['nombre'] = 'El nombre interno es obligatorio.'
        if not etiqueta:
            errores['etiqueta'] = 'La etiqueta visible es obligatoria.'
        if not tipo:
            errores['tipo'] = 'El tipo de campo es obligatorio.'
        
        # Verificar que el nombre no exista ya para esta entidad (excepto este mismo campo)
        if nombre and CampoEntidadFinanciera.objects.filter(
            entidad=entidad, nombre=nombre
        ).exclude(pk=campo.id).exists():
            errores['nombre'] = 'Ya existe otro campo con este nombre para esta entidad.'
        
        if errores:
            campo_temp = CampoEntidadFinanciera(
                id=campo.id, entidad=entidad, nombre=nombre, etiqueta=etiqueta, 
                tipo=tipo, requerido=requerido, orden=orden, 
                regex_validacion=regex_validacion, mensaje_error=mensaje_error, 
                placeholder=placeholder, ayuda=ayuda
            )
            html = render_to_string('medio_acreditacion/campo_entidad_form.html', 
                                  {'campo': campo_temp, 'entidad': entidad, 'errores': errores}, 
                                  request=request)
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'html': html})
            return render(request, 'medio_acreditacion/campo_entidad_form.html', 
                        {'campo': campo_temp, 'entidad': entidad, 'errores': errores})
        
        # Actualizar el campo
        campo.nombre = nombre
        campo.etiqueta = etiqueta
        campo.tipo = tipo
        campo.requerido = requerido
        campo.orden = orden
        campo.regex_validacion = regex_validacion
        campo.mensaje_error = mensaje_error
        campo.placeholder = placeholder
        campo.ayuda = ayuda
        campo.save()
        
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            campos = entidad.campos.all().order_by('orden')
            html = render_to_string('medio_acreditacion/partials/campos_entidad_table.html', 
                                  {'campos': campos, 'entidad': entidad}, 
                                  request=request)
            return JsonResponse({'success': True, 'html': html})
        
        messages.success(request, 'Campo actualizado correctamente.')
        return redirect('campos_entidad_list', entidad_id=entidad.id)
    
    # GET request
    html = render_to_string('medio_acreditacion/campo_entidad_form.html', 
                          {'campo': campo, 'entidad': entidad, 'errores': {}}, 
                          request=request)
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'success': False, 'html': html})
    return render(request, 'medio_acreditacion/campo_entidad_form.html', 
                {'campo': campo, 'entidad': entidad, 'errores': {}})


def campo_entidad_delete(request, campo_id):
    """
    Elimina un campo personalizado de una entidad financiera.

    Si la solicitud proviene por AJAX, devuelve la tabla actualizada.
    En caso contrario, redirige a la lista de campos.

    :param request: Objeto HttpRequest.
    :param campo_id: ID del campo a eliminar.
    :return: JsonResponse o HttpResponseRedirect según el contexto.
    """
    campo = get_object_or_404(CampoEntidadFinanciera, pk=campo_id)
    entidad = campo.entidad
    
    if request.method == 'POST':
        campo.delete()
        
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            campos = entidad.campos.all().order_by('orden')
            html = render_to_string('medio_acreditacion/partials/campos_entidad_table.html', 
                                  {'campos': campos, 'entidad': entidad}, 
                                  request=request)
            return JsonResponse({'success': True, 'html': html})
        
        messages.success(request, 'Campo eliminado correctamente.')
        return redirect('campos_entidad_list', entidad_id=entidad.id)
    
    # Para peticiones GET (no debería llegar aquí normalmente)
    return redirect('campos_entidad_list', entidad_id=entidad.id)