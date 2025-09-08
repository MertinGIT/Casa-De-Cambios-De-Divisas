"""
VISTAS PARA GESTIÓN DE ASIGNACIONES CLIENTE-USUARIO
=================================================

Este módulo contiene todas las vistas para gestionar las asignaciones entre
clientes y usuarios del sistema, permitiendo establecer relaciones de 
responsabilidad y acceso.

Funcionalidades principales:
- Lista de asignaciones existentes con búsqueda avanzada
- Edición de asignaciones cliente-usuario
- Vista AJAX para obtener detalles de asignaciones
- Gestión de relaciones many-to-many
- Búsqueda por nombre de cliente y usuarios asignados

Arquitectura:
- Vistas basadas en funciones (FBV) para operaciones específicas
- Integración con modelos Cliente y CustomUser
- Soporte para operaciones AJAX
- Formularios dinámicos con precarga de datos
- Búsqueda con Django Q objects

Modelos relacionados:
- Cliente: Entidad principal del cliente
- CustomUser: Usuario del sistema
- Relación Many-to-Many: Cliente.usuarios
"""

from functools import wraps
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from usuarios.models import CustomUser
from .forms import ClienteUsuariosForm
from clientes.models import Cliente
import logging

logger = logging.getLogger(__name__)

# Listar asignaciones
def cliente_usuarios_lista(request):
    """
    Vista principal que muestra la lista de asignaciones entre usuarios y clientes.

    Esta vista renderiza la página principal del módulo de asignaciones,
    mostrando todos los clientes con sus usuarios asignados y proporcionando
    un formulario para crear nuevas asignaciones. Incluye funcionalidad de
    búsqueda avanzada por nombre de cliente y usuarios asignados.

    Funcionalidades:
    - Lista todos los clientes ordenados por ID descendente
    - Búsqueda por nombre de cliente o usuarios asignados
    - Filtrado específico por campo seleccionado
    - Paginación de resultados (8 elementos por página)
    - Muestra usuarios disponibles para asignación
    - Proporciona formulario vacío para nuevas asignaciones
    - Mantiene estado de búsqueda en la interfaz

    Parámetros GET soportados:
    - q: Término de búsqueda
    - campo: Campo específico donde buscar ('cliente', 'usuario')
    - page: Número de página para paginación

    Args:
        request (HttpRequest): Objeto de petición HTTP

    Returns:
        HttpResponse: Página renderizada con la lista de asignaciones

    Context variables:
        usuarios (QuerySet): Todos los usuarios del sistema
        clientes (QuerySet): Clientes paginados y filtrados
        form (ClienteUsuariosForm): Formulario vacío para nuevas asignaciones
        q (str): Término de búsqueda actual
        campo_selected (str): Campo de búsqueda seleccionado
        page_obj: Objeto de paginación
        is_paginated (bool): Indica si hay paginación

    Template:
        lista.html: Template principal con tabla de asignaciones

    Ejemplo de uso:
        URL: /cliente-usuario/?q=juan&campo=cliente
        Método: GET
        Resultado: Página con clientes que contienen "juan" en el nombre
    """
    # Obtener y limpiar parámetros de búsqueda
    q = request.GET.get('q', '').strip()
    campo = request.GET.get('campo', '').strip()
    
    # QuerySet base ordenado por más recientes
    clientes_queryset = Cliente.objects.all().order_by('-id')
    
    # Aplicar filtros de búsqueda si existe término de búsqueda
    if q:
        clientes_queryset = clientes_queryset.filter(
                Q(nombre__icontains=q)
            )
    # Configurar paginación
    paginator = Paginator(clientes_queryset, 8)  # 8 clientes por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Obtener todos los usuarios disponibles ordenados alfabéticamente
    usuarios = CustomUser.objects.all().order_by('username')
    
    # Inicializar formulario vacío para nuevas asignaciones
    form = ClienteUsuariosForm()
    
    return render(request, 'lista.html', {
        'usuarios': usuarios,
        'clientes': page_obj,  # Usar page_obj en lugar de queryset completo
        'form': form,
        'q': q,  # Mantener término de búsqueda en template
        'campo_selected': campo,  # Mantener campo seleccionado
        'page_obj': page_obj,  # Para controles de paginación
        'is_paginated': page_obj.has_other_pages(),  # Flag de paginación
    })


# Editar asignación
def editar_cliente_usuario(request, id):
    """
    Vista para editar una asignación existente entre un usuario y un cliente.

    Esta vista maneja tanto la visualización del formulario de edición como
    el procesamiento de los datos enviados. Utiliza un modal para mostrar
    el formulario y permite modificar los usuarios asignados a un cliente.
    Mantiene los parámetros de búsqueda después de la edición.

    Funcionalidades:
    - Carga datos existentes del cliente
    - Muestra usuarios actualmente asignados
    - Procesa cambios en las asignaciones
    - Valida y guarda modificaciones
    - Maneja errores de validación
    - Preserva estado de búsqueda al redirigir

    Args:
        request (HttpRequest): Objeto de petición HTTP
        id (int): ID del cliente cuya asignación se desea editar

    Returns:
        HttpResponse: 
            - POST válido: Redirect a lista de asignaciones con parámetros de búsqueda
            - GET o POST inválido: Página con modal de edición abierto

    Context variables:
        form (ClienteUsuariosForm): Formulario con datos del cliente
        usuarios (QuerySet): Todos los usuarios disponibles
        usuarios_asignados (list): IDs de usuarios asignados al cliente
        show_modal (bool): Flag para mostrar modal automáticamente
        modal_type (str): Tipo de modal ('edit')
        obj_id (int): ID del cliente en edición
        q (str): Término de búsqueda para mantener estado
        campo_selected (str): Campo de búsqueda para mantener estado

    Excepciones:
        Http404: Si no existe cliente con el ID proporcionado

    Flujo de ejecución:
        1. Obtiene cliente por ID (404 si no existe)
        2. Si es POST: valida formulario y guarda cambios
        3. Construye URL de redirección con parámetros de búsqueda
        4. Si es GET: prepara formulario con datos existentes
        5. Obtiene usuarios asignados actuales
        6. Renderiza template con modal abierto

    Ejemplo de uso:
        URL: /cliente-usuario/editar/123/?q=juan&campo=cliente
        Método: POST con datos de usuarios seleccionados
        Resultado: Asignaciones actualizadas y redirect con búsqueda preservada
    """
    # Obtener cliente o devolver 404 si no existe
    cliente = get_object_or_404(Cliente, id=id)
    
    # Obtener parámetros de búsqueda para mantener estado
    q = request.GET.get('q', '')
    campo = request.GET.get('campo', '')

    if request.method == "POST":
        # Procesar formulario enviado
        form = ClienteUsuariosForm(request.POST, instance=cliente)
        if form.is_valid():
            try:
                # Guardar cambios en asignaciones
                form.save()
                messages.success(request, "Asignación actualizada correctamente.")
                
                # Construir URL de redirección manteniendo parámetros de búsqueda
                redirect_url = "cliente_usuario"
                params = []
                if q:
                    params.append(f"q={q}")
                if campo:
                    params.append(f"campo={campo}")
                
                if params:
                    redirect_url += "?" + "&".join(params)
                    
                return redirect(redirect_url)
            except Exception as e:
                logger.error(f"Error actualizando asignación cliente {id}: {e}")
                messages.error(request, "Error al actualizar la asignación.")
        else:
            # Mostrar errores de validación
            messages.error(request, "Por favor corrige los errores en el formulario.")
    else:
        # Inicializar formulario con datos existentes
        form = ClienteUsuariosForm(instance=cliente)

    # Obtener todos los usuarios ordenados alfabéticamente
    usuarios_all = CustomUser.objects.all().order_by('username')
    
    # Obtener IDs de usuarios actualmente asignados al cliente
    usuarios_asignados = list(cliente.usuarios.values_list('id', flat=True))
    
    return render(request, "lista.html", {
        "form": form,
        "usuarios": usuarios_all,
        "usuarios_asignados": usuarios_asignados,
        "show_modal": True,
        "modal_type": "edit",
        "obj_id": cliente.id,
        "q": q,  # Mantener búsqueda en template
        "campo_selected": campo,  # Mantener campo seleccionado
    })


# Vista para obtener datos de un rol via AJAX (para llenar el modal de edición)
def cliente_usuario_detalle(request, pk):
    """
    Vista AJAX para obtener detalles de asignaciones de un cliente específico.

    Esta vista proporciona una API interna para obtener información de
    asignaciones de usuario de un cliente específico en formato JSON.
    Principalmente utilizada para cargar datos en modales de edición
    mediante peticiones AJAX.

    Funcionalidades:
    - Obtiene usuario asignados a un cliente
    - Convierte IDs a strings para compatibilidad JSON
    - Proporciona título para modal de edición
    - Manejo de errores con respuesta 404

    Args:
        request (HttpRequest): Objeto de petición HTTP (debe ser AJAX)
        pk (int): Primary key del cliente

    Returns:
        JsonResponse: Respuesta JSON con datos de asignación

    Response format:
        {
            "usuarios": ["1", "2", "3"],  // IDs como strings
            "modal_title": "Editar Asignación"
        }

    Excepciones:
        Http404: Si no existe cliente con el pk proporcionado

    Casos de uso:
        - Cargar datos en modal de edición sin recargar página
        - Obtener información rápida de asignaciones
        - Integración con JavaScript frontend
        - APIs internas para componentes dinámicos

    Consideraciones técnicas:
        - Los IDs se convierten a string para evitar problemas JSON
        - Response es compatible con jQuery y fetch API
        - Manejo automático de serialización JSON por Django

    Ejemplo de uso:
        // JavaScript
        fetch('/cliente-usuario/detalle/123/')
            .then(response => response.json())
            .then(data => {
                console.log(data.usuarios); // ["1", "5", "8"]
                document.title = data.modal_title;
            });

    Seguridad:
        - Requiere autenticación implícita del sistema
        - No expone información sensible
        - Solo devuelve IDs públicos
    """
    # Obtener cliente o devolver 404
    cliente = get_object_or_404(Cliente, pk=pk)
    
    # Obtener IDs de usuarios asignados y convertir a strings
    # La conversión a string evita problemas de serialización JSON
    usuarios_ids = list(map(str, cliente.usuarios.values_list('id', flat=True)))
    
    # Preparar respuesta JSON
    response_data = {
        "usuarios": usuarios_ids,
        "modal_title": "Editar Asignación"
    }
    
    return JsonResponse(response_data)
