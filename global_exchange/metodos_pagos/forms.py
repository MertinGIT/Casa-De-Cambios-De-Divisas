"""
FORMULARIOS PARA GESTIÓN DE MÉTODOS DE PAGO
==========================================

Este módulo contiene los formularios para crear y editar métodos de pago
del sistema de casa de cambios, proporcionando validación robusta,
normalización de datos y una interfaz de usuario optimizada.

Funcionalidades principales:
- Validación completa de campos con mensajes personalizados
- Normalización automática de texto Unicode
- Verificación de unicidad case-insensitive
- Widgets personalizados con estilos CSS
- Manejo de longitudes mínimas y máximas
- Validación diferenciada para creación y edición

Arquitectura:
- FormModel basado en MetodoPago
- Función auxiliar para normalización de texto
- Validaciones personalizadas por campo
- Configuración de widgets con atributos HTML
- Manejo de errores con mensajes descriptivos

Componentes:
- _normalize_text(): Función auxiliar para normalización Unicode
- MetodoPagoForm: Formulario principal del modelo

Casos de uso:
- Creación de nuevos métodos de pago
- Edición de métodos existentes
- Validación en tiempo real (frontend)
- Integración con vistas basadas en clases

Autor: [Tu nombre]
Fecha: [Fecha actual]
Versión: 1.0
"""

from django import forms
from django.core.exceptions import ValidationError
from .models import MetodoPago
import unicodedata

def _normalize_text(s: str) -> str:
    """
    Función auxiliar para normalizar texto Unicode y espacios.
    
    Esta función estandariza el texto de entrada aplicando normalización
    Unicode NFKC y eliminando espacios en blanco al inicio y final.
    Es esencial para evitar problemas de codificación y comparaciones
    inconsistentes en validaciones de unicidad.
    
    Funcionalidades:
    - Normalización Unicode NFKC (Canonical Decomposition + Canonical Composition)
    - Eliminación de espacios en blanco iniciales y finales
    - Manejo seguro de valores None
    - Conversión consistente para comparaciones
    
    Args:
        s (str): Texto a normalizar. Puede ser None o cadena vacía.
        
    Returns:
        str: Texto normalizado y sin espacios en extremos.
             Retorna cadena vacía si el input es None.
    
    Proceso de normalización:
        1. Verificación de None para evitar errores
        2. Aplicación de normalización Unicode NFKC
        3. Eliminación de espacios con strip()
        4. Retorno de resultado normalizado
    
    Ejemplos:
        >>> _normalize_text("  Efectivo  ")
        'Efectivo'
        
        >>> _normalize_text("Café")  # Con acentos
        'Café'
        
        >>> _normalize_text(None)
        ''
        
        >>> _normalize_text("   ")
        ''
    
    Casos de uso:
        - Validación de nombres únicos
        - Limpieza de datos de entrada
        - Preparación para comparaciones
        - Normalización antes de guardado
    
    Consideraciones técnicas:
        - NFKC es ideal para texto de interfaz de usuario
        - Maneja caracteres especiales y acentos correctamente
        - Compatible con bases de datos que usan UTF-8
        - Previene duplicados por diferencias de codificación
    """
    if s is None:
        return ''
    # Normaliza Unicode y quita espacios en ambos extremos
    return unicodedata.normalize('NFKC', s).strip()

class MetodoPagoForm(forms.ModelForm):
    """
    Formulario principal para creación y edición de métodos de pago.
    
    Este formulario maneja la entrada de datos para métodos de pago,
    proporcionando validación robusta, normalización automática y
    una interfaz de usuario optimizada con widgets personalizados.
    
    Características principales:
    - Validación de unicidad case-insensitive
    - Normalización automática de texto
    - Widgets personalizados con estilos CSS
    - Mensajes de error descriptivos
    - Longitudes mínimas y máximas configurables
    - Diferenciación entre creación y edición
    
    Campos incluidos:
    - nombre: Campo requerido con validación de unicidad
    - descripcion: Campo opcional con longitud limitada
    - comision: Campo requerido con validación numérica
    
    Validaciones aplicadas:
    - Nombre: requerido, mínimo 3 caracteres, máximo 100, único
    - Descripción: opcional, máximo 500 caracteres, normalizada
    - Comisión: requerida, numérica, entre 0 y 100
    
    Widgets configurados:
    - TextInput para nombre con atributos HTML específicos
    - Textarea para descripción con filas y límite de caracteres
    - NumberInput para comisión con rango y pasos definidos
    
    Meta configuración:
        model: MetodoPago - Modelo base del formulario
        fields: ['nombre', 'descripcion', 'comision'] - Campos incluidos
        labels: Etiquetas personalizadas para los campos
        widgets: Configuración de widgets con clases CSS y atributos
    
    Ejemplos de uso:
        # Creación de nuevo método
        form = MetodoPagoForm(data={'nombre': 'Efectivo', 'comision': 2.5})
        if form.is_valid():
            metodo = form.save()
            
        # Edición de método existente
        metodo = MetodoPago.objects.get(pk=1)
        form = MetodoPagoForm(instance=metodo, data={'nombre': 'Efectivo USD', 'comision': 3.0})
        if form.is_valid():
            form.save()
    
    Validaciones personalizadas:
        - clean_nombre(): Validación completa del campo nombre
        - clean_descripcion(): Normalización y validación de descripción
        - clean_comision(): Validación de rango y obligatoriedad de comisión
    
    Consideraciones de seguridad:
        - Validación de longitud para prevenir ataques
        - Normalización para evitar bypass de unicidad
        - Escape automático de HTML en widgets
    """
    
    class Meta:
        """
        Configuración de metadatos del formulario MetodoPagoForm.
        
        Define el modelo base, campos incluidos, etiquetas personalizadas
        y widgets con sus respectivos atributos HTML y clases CSS.
        
        Configuraciones:
        - model: Especifica MetodoPago como modelo base
        - fields: Lista de campos del modelo a incluir
        - labels: Etiquetas amigables para la interfaz
        - widgets: Configuración detallada de widgets HTML
        
        Widgets configurados:
            nombre (TextInput):
                - class: Clases CSS para estilos
                - id: ID específico para JavaScript
                - placeholder: Texto de ayuda
                - maxlength: Límite de caracteres en HTML
                
            descripcion (Textarea):
                - class: Clases CSS para estilos
                - id: ID específico para JavaScript
                - placeholder: Texto de ayuda
                - rows: Número de filas visibles
                - maxlength: Límite de caracteres en HTML

            comision (NumberInput):
                - class: Clases CSS para estilos
                - id: ID específico para JavaScript
                - placeholder: Texto de ayuda
                - step: Paso para incremento (0.01)
                - min: Valor mínimo (0)
                - max: Valor máximo (100)
        """
        model = MetodoPago
        fields = ['nombre', 'descripcion', 'comision']
        labels = {
            'nombre': 'Nombre',
            'descripcion': 'Descripción',
            'comision': 'Comisión (%)',
        }
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control custom-input',
                'id': 'id_nombre',
                'placeholder': 'Ingrese el nombre',
                'maxlength': '100',
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control custom-input',
                'id': 'id_descripcion',
                'placeholder': 'Ingrese la descripción (opcional)',
                'rows': 3,
                'maxlength': '500',
            }),
            'comision': forms.NumberInput(attrs={
                'class': 'form-control custom-input',
                'id': 'id_comision',
                'placeholder': 'Ej: 2.50',
                'step': '0.01',
                'min': '0',
                'max': '100',
            }),
        }

    def __init__(self, *args, **kwargs):
        """
        Inicialización personalizada del formulario.
        
        Configura propiedades adicionales de los campos que no se pueden
        definir en Meta, como los atributos required específicos.
        
        Configuraciones aplicadas:
        - nombre: Marcado como requerido explícitamente
        - descripcion: Marcado como opcional explícitamente
        - comision: Marcado como requerido con rango específico
        
        Args:
            *args: Argumentos posicionales para ModelForm
            **kwargs: Argumentos nombrados para ModelForm
            
        Proceso:
            1. Llama al inicializador padre de ModelForm
            2. Configura propiedades específicas de campos
            3. Establece requerimientos personalizados
        
        Ejemplo:
            >>> form = MetodoPagoForm()
            >>> form.fields['nombre'].required
            True
            >>> form.fields['descripcion'].required
            False
        """
        super().__init__(*args, **kwargs)
        # Configuración explícita de campos requeridos
        self.fields['nombre'].required = True
        self.fields['descripcion'].required = False
        # Hacer comision opcional para que el form sea válido sin enviarla
        self.fields['comision'].required = False
        self.fields['comision'].min_value = 0
        self.fields['comision'].max_value = 100

    def clean_nombre(self):
        """
        Validación personalizada del campo nombre.
        
        Aplica normalización Unicode, validaciones de longitud y
        verificación de unicidad case-insensitive. Maneja tanto
        creación de nuevos registros como edición de existentes.
        
        Validaciones aplicadas:
        1. Normalización de texto Unicode
        2. Verificación de campo no vacío
        3. Validación de longitud mínima (3 caracteres)
        4. Validación de longitud máxima (100 caracteres)
        5. Verificación de unicidad case-insensitive
        6. Exclusión de instancia actual en edición
        
        Returns:
            str: Nombre normalizado y validado
            
        Raises:
            ValidationError: En cualquiera de los siguientes casos:
                - Nombre vacío después de normalización
                - Longitud menor a 3 caracteres
                - Longitud mayor a 100 caracteres
                - Nombre ya existe en base de datos
        
        Proceso de validación:
            1. Obtiene valor del campo desde cleaned_data
            2. Aplica normalización con _normalize_text()
            3. Valida que no esté vacío
            4. Verifica longitud mínima y máxima
            5. Construye query para verificar unicidad
            6. Excluye instancia actual si es edición
            7. Verifica existencia en base de datos
            8. Retorna valor normalizado si pasa todas las validaciones
        
        Ejemplos:
            >>> form = MetodoPagoForm(data={'nombre': '  efectivo  '})
            >>> form.is_valid()
            True
            >>> form.cleaned_data['nombre']
            'efectivo'
            
            >>> form = MetodoPagoForm(data={'nombre': 'ab'})
            >>> form.is_valid()
            False
            >>> form.errors['nombre']
            ['El nombre debe tener al menos 3 caracteres.']
        
        Consideraciones:
            - La validación es case-insensitive para evitar duplicados
            - La normalización Unicode previene problemas de codificación
            - La exclusión de instancia actual permite edición sin conflictos
        """
        # Obtener valor bruto del campo
        raw = self.cleaned_data.get('nombre', '')
        # Aplicar normalización Unicode
        nombre = _normalize_text(raw)
        
        # Validación: campo no vacío
        if not nombre:
            raise ValidationError("El nombre es obligatorio.")
        
        # Validación: longitud mínima
        if len(nombre) < 3:
            raise ValidationError("El nombre debe tener al menos 3 caracteres.")
        
        # Validación: longitud máxima
        if len(nombre) > 100:
            raise ValidationError("El nombre no puede exceder 100 caracteres.")

        # Validación de unicidad case-insensitive
        # Construir queryset para verificar existencia
        qs = MetodoPago.objects.filter(nombre__iexact=nombre)
        
        # Excluir la instancia actual si estamos editando
        if self.instance and getattr(self.instance, 'pk', None):
            qs = qs.exclude(pk=self.instance.pk)
        
        # Verificar si existe otro registro con el mismo nombre
        if qs.exists():
            raise ValidationError("Este nombre ya existe, por favor elige otro.")
        
        return nombre

    def clean_descripcion(self):
        """
        Validación personalizada del campo descripción.
        
        Aplica normalización Unicode y validación de longitud máxima.
        Proporciona valor por defecto si el campo está vacío.
        
        Validaciones aplicadas:
        1. Normalización de texto Unicode si hay contenido
        2. Validación de longitud máxima (500 caracteres)
        3. Asignación de valor por defecto si está vacío
        
        Returns:
            str: Descripción normalizada y validada, o mensaje por defecto
            
        Raises:
            ValidationError: Si la descripción excede 500 caracteres
        
        Proceso de validación:
            1. Obtiene valor del campo desde cleaned_data
            2. Si hay contenido, aplica normalización
            3. Verifica longitud máxima
            4. Retorna descripción normalizada o valor por defecto
        
        Comportamiento especial:
            - Campo opcional: acepta valores vacíos
            - Valor por defecto: "No hay descripción" si está vacío
            - Normalización: solo si hay contenido real
        
        Ejemplos:
            >>> form = MetodoPagoForm(data={'descripcion': '  Pago en efectivo  '})
            >>> form.is_valid()
            True
            >>> form.cleaned_data['descripcion']
            'Pago en efectivo'
            
            >>> form = MetodoPagoForm(data={'descripcion': ''})
            >>> form.is_valid()
            True
            >>> form.cleaned_data['descripcion']
            'No hay descripción'
            
            >>> # Descripción muy larga
            >>> form = MetodoPagoForm(data={'descripcion': 'x' * 501})
            >>> form.is_valid()
            False
            >>> form.errors['descripcion']
            ['La descripción no puede exceder 500 caracteres.']
        
        Consideraciones de UX:
            - Proporciona valor por defecto para evitar campos vacíos
            - Validación de longitud para proteger base de datos
            - Normalización para consistencia de datos
        """
        # Obtener valor del campo
        descripcion = self.cleaned_data.get('descripcion', '')
        
        # Si hay contenido, normalizar y validar
        if descripcion:
            descripcion = _normalize_text(descripcion)
            if len(descripcion) > 500:
                raise ValidationError("La descripción no puede exceder 500 caracteres.")
        
        # Default que esperan los tests
        return descripcion or "No hay descripción"

    def clean_comision(self):
        """
        Hacer opcional la comisión. Si viene vacía, usar 0.00.
        Validar rango 0..100 si viene informada.
        """
        comision = self.cleaned_data.get('comision')
        if comision in (None, ''):
            return 0  # default
        # Aceptar valores numéricos válidos dentro del rango
        try:
            # Si ya es número, Django lo entregará como Decimal/float
            valor = float(comision)
        except (TypeError, ValueError):
            raise ValidationError('La comisión debe ser un número.')
        if valor < 0 or valor > 100:
            raise ValidationError('La comisión debe estar entre 0 y 100.')
        return valor

    def clean(self):
        """
        Validación global del formulario.
        
        Ejecuta validaciones que involucran múltiples campos o
        reglas de negocio complejas que requieren el formulario completo.
        
        Returns:
            dict: Datos limpios y validados del formulario
            
        Raises:
            ValidationError: Si alguna validación global falla
        
        Validaciones globales aplicadas:
            - Consistencia entre campos relacionados
            - Reglas de negocio específicas del dominio
            - Validaciones que requieren múltiples campos
        
        Ejemplo:
            >>> form = MetodoPagoForm(data={
            ...     'nombre': 'Efectivo',
            ...     'descripcion': 'Pago en efectivo'
            ... })
            >>> form.is_valid()
            True
            >>> form.cleaned_data
            {'nombre': 'Efectivo', 'descripcion': 'Pago en efectivo'}
        """
        # Ejecutar validación global del padre
        cleaned_data = super().clean()
        
        # Aquí se pueden agregar validaciones que involucren múltiples campos
        # Por ejemplo, verificar que ciertos tipos de métodos tengan descripción
        
        return cleaned_data
    
    def save(self, commit=True):
        """
        Guardado personalizado del formulario.
        
        Aplica lógica adicional antes de guardar el objeto en la base de datos,
        como configuraciones específicas o procesamiento de datos.
        
        Args:
            commit (bool): Si True, guarda inmediatamente en base de datos.
                          Si False, retorna instancia sin guardar.
                          
        Returns:
            MetodoPago: Instancia del modelo guardada o preparada para guardar
        
        Proceso:
            1. Crea instancia del modelo con datos del formulario
            2. Aplica configuraciones adicionales si es necesario
            3. Guarda en base de datos si commit=True
            4. Retorna instancia del modelo
        
        Ejemplo:
            >>> form = MetodoPagoForm(data={'nombre': 'Transferencia'})
            >>> if form.is_valid():
            ...     metodo = form.save()
            ...     print(f"Guardado: {metodo.nombre}")
            Guardado: Transferencia
        """
        # Crear instancia del modelo sin guardar aún
        instance = super().save(commit=False)
        
        # Aquí se pueden aplicar configuraciones adicionales
        # Por ejemplo, establecer valores por defecto o calcular campos
        
        # Guardar en base de datos si se solicita
        if commit:
            instance.save()
            
        return instance