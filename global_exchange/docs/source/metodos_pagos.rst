Métodos de Pago
===============

.. automodule:: metodos_pagos
   :members:
   :undoc-members:
   :show-inheritance:

Descripción General
-------------------

El módulo de métodos de pago proporciona un sistema completo de gestión para los diferentes tipos de pago que acepta la casa de cambio. Incluye funcionalidades de CRUD completo, búsqueda avanzada, validación en tiempo real y control de acceso.

Características Principales
---------------------------

* **CRUD Completo**: Crear, leer, actualizar y desactivar métodos de pago
* **Búsqueda Avanzada**: Filtros por nombre y descripción con paginación
* **Validación Robusta**: Verificación de unicidad y normalización Unicode
* **Soft Delete**: Desactivación en lugar de eliminación física
* **Control de Acceso**: Restricción a superadministradores
* **Interfaz Optimizada**: Widgets personalizados y validación AJAX

Modelos
-------

MetodoPago
^^^^^^^^^^

.. automodule:: metodos_pagos.models
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: metodos_pagos.models.MetodoPago
   :members:
   :undoc-members:
   :show-inheritance:
   
   **Campos del modelo:**
   
   * **nombre** (CharField): Nombre único del método de pago, máximo 100 caracteres
   * **descripcion** (TextField): Descripción detallada, opcional
   * **activo** (BooleanField): Estado de disponibilidad, por defecto True
   
   **Métodos de clase:**
   
   * ``activos()``: Retorna QuerySet de métodos activos
   * ``inactivos()``: Retorna QuerySet de métodos inactivos
   
   **Propiedades:**
   
   * ``estado_texto``: Retorna "Activo" o "Inactivo" según el estado

Formularios
-----------

MetodoPagoForm
^^^^^^^^^^^^^^

.. automodule:: metodos_pagos.forms
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: metodos_pagos.forms.MetodoPagoForm
   :members:
   :undoc-members:
   :show-inheritance:
   
   **Validaciones implementadas:**
   
   * Normalización automática de texto Unicode
   * Verificación de unicidad case-insensitive
   * Longitud mínima de 3 caracteres para el nombre
   * Longitud máxima de 500 caracteres para descripción
   * Manejo diferenciado entre creación y edición

Funciones Auxiliares
^^^^^^^^^^^^^^^^^^^^

.. autofunction:: metodos_pagos.forms._normalize_text

   Función para normalizar texto Unicode y eliminar espacios en extremos.
   Esencial para validaciones de unicidad consistentes.

Vistas
------

.. automodule:: metodos_pagos.views
   :members:
   :undoc-members:
   :show-inheritance:

Decoradores
^^^^^^^^^^^

.. autofunction:: metodos_pagos.views.superadmin_required

   Decorador personalizado que restringe acceso solo a superusuarios.

Vistas Basadas en Clases
^^^^^^^^^^^^^^^^^^^^^^^^

.. autoclass:: metodos_pagos.views.MetodoPagoListView
   :members:
   :undoc-members:
   
   **Funcionalidades:**
   
   * Paginación automática (8 elementos por página)
   * Búsqueda por nombre y descripción
   * Filtrado específico por campo seleccionado
   * Mantenimiento de estado de búsqueda

.. autoclass:: metodos_pagos.views.MetodoPagoCreateView
   :members:
   :undoc-members:
   
   Vista para crear nuevos métodos de pago con validación completa.

.. autoclass:: metodos_pagos.views.MetodoPagoUpdateView
   :members:
   :undoc-members:
   
   Vista para editar métodos existentes manteniendo validaciones.

.. autoclass:: metodos_pagos.views.MetodoPagoDesactivateView
   :members:
   :undoc-members:
   
   Vista para desactivar métodos (soft delete) sin eliminar registros.

.. autoclass:: metodos_pagos.views.MetodoPagoActivateView
   :members:
   :undoc-members:
   
   Vista para reactivar métodos previamente desactivados.

Vistas Funcionales
^^^^^^^^^^^^^^^^^^

.. autofunction:: metodos_pagos.views.metodos_pagos

   Vista funcional simple para renderizar la lista (en desuso).

.. autofunction:: metodos_pagos.views.MetodoPago_detalle

   Vista AJAX para obtener detalles de un método de pago específico.

.. autofunction:: metodos_pagos.views.validar_nombre_metodo_pago

   Vista AJAX para validar unicidad del nombre en tiempo real.

URLs y Endpoints
----------------

El módulo proporciona los siguientes endpoints:

* ``/metodos-pagos/`` - Lista principal con búsqueda y paginación
* ``/metodos-pagos/agregar/`` - Formulario de creación
* ``/metodos-pagos/editar/<id>/`` - Formulario de edición
* ``/metodos-pagos/desactivar/<id>/`` - Desactivar método de pago
* ``/metodos-pagos/activar/<id>/`` - Activar método de pago
* ``/metodos-pagos/detalle/<id>/`` - API AJAX para detalles
* ``/metodos-pagos/validar-nombre/`` - Validación AJAX de nombres

Parámetros de Búsqueda
----------------------

La lista principal acepta los siguientes parámetros GET:

* ``q``: Término de búsqueda
* ``campo``: Campo específico donde buscar ('nombre', 'descripcion')
* ``page``: Número de página para paginación

Ejemplos de Uso
---------------

Crear Método de Pago
^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   # Usando el formulario
   form = MetodoPagoForm(data={
       'nombre': 'Transferencia Bancaria',
       'descripcion': 'Transferencia a cuenta bancaria nacional'
   })
   if form.is_valid():
       metodo = form.save()

   # Directamente con el modelo
   metodo = MetodoPago.objects.create(
       nombre="Efectivo",
       descripcion="Pago en efectivo en oficina",
       activo=True
   )

Búsqueda y Filtrado
^^^^^^^^^^^^^^^^^^

.. code-block:: python

   # Obtener métodos activos
   activos = MetodoPago.activos()

   # Búsqueda por nombre
   resultados = MetodoPago.objects.filter(nombre__icontains='efectivo')

   # Usar en vista con búsqueda
   # URL: /metodos-pagos/?q=transferencia&campo=nombre

Validación AJAX
^^^^^^^^^^^^^^^

.. code-block:: javascript

   // Validar nombre en tiempo real
   $.post('/metodos-pagos/validar-nombre/', {
       'nombre': 'Nuevo Método',
       'current_id': '123'  // Para edición
   }, function(data) {
       if (data.valid) {
           console.log('Nombre disponible');
       } else {
           console.log('Error: ' + data.message);
       }
   });

Soft Delete
^^^^^^^^^^^

.. code-block:: python

   # Desactivar método (soft delete)
   metodo = MetodoPago.objects.get(pk=1)
   metodo.activo = False
   metodo.save()

   # Reactivar método
   metodo.activo = True
   metodo.save()

Consideraciones Técnicas
------------------------

**Rendimiento:**

* Índices en campos 'nombre' y 'activo' para consultas rápidas
* Paginación para listas grandes
* Consultas optimizadas con select_related cuando sea necesario

**Seguridad:**

* Validación de entrada en formularios y vistas
* Control de acceso mediante decorador superadmin_required
* Normalización Unicode para prevenir bypass de validaciones
* Escape automático de HTML en templates

**Mantenimiento:**

* Soft delete para preservar integridad referencial
* Logging de errores para debugging
* Mensajes descriptivos para usuarios
* Documentación completa en código

Errores Comunes
---------------

1. **Nombre Duplicado**: Cada método debe tener un nombre único
2. **Permisos Insuficientes**: Solo superadministradores pueden gestionar métodos
3. **Validación Unicode**: Problemas con caracteres especiales se resuelven con normalización
4. **Soft Delete**: Los métodos desactivados siguen en la base de datos
5. **Búsqueda Case-Sensitive**: Las búsquedas son case-insensitive por defecto

Migración y Deployment
---------------------

**Migración inicial:**

.. code-block:: bash

   python manage.py makemigrations metodos_pagos
   python manage.py migrate

**Datos de prueba:**

.. code-block:: python

   # Crear métodos básicos
   MetodoPago.objects.get_or_create(
       nombre="Efectivo",
       defaults={'descripcion': 'Pago en efectivo'}
   )
   MetodoPago.objects.get_or_create(
       nombre="Transferencia",
       defaults={'descripcion': 'Transferencia bancaria'}
   )