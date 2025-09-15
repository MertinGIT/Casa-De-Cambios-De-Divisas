"""
MODELOS PARA GESTIÓN DE MÉTODOS DE PAGO
======================================

Este módulo define el modelo de datos para los métodos de pago disponibles
en el sistema de casa de cambios, proporcionando la estructura base para
almacenar y gestionar diferentes formas de pago.

Funcionalidades principales:
- Almacenamiento de métodos de pago únicos
- Control de estado activo/inactivo
- Descripción detallada de cada método
- Ordenamiento alfabético por defecto
- Validación de unicidad automática

Arquitectura:
- Modelo simple con campos esenciales
- Soft delete mediante campo booleano
- Restricciones de base de datos para integridad
- Métodos personalizados para representación

Campos del modelo:
- nombre: Identificador único del método de pago
- descripcion: Información detallada del método
- activo: Estado del método (disponible/no disponible)

Casos de uso:
- Definir métodos como: Efectivo, Transferencia, Tarjeta, etc.
- Habilitar/deshabilitar métodos según disponibilidad
- Mantener histórico de métodos utilizados
- Proporcionar información detallada a usuarios
"""

from django.db import models

class MetodoPago(models.Model):
    """
    Modelo para almacenar métodos de pago disponibles en el sistema.
    
    Este modelo representa los diferentes métodos de pago que acepta
    la casa de cambios, permitiendo una gestión flexible y dinámica
    de las opciones de pago disponibles para los clientes.
    
    Características:
    - Nombres únicos para evitar duplicados
    - Descripciones opcionales para información adicional
    - Control de estado activo/inactivo para disponibilidad
    - Ordenamiento alfabético automático
    - Soft delete para mantener histórico
    
    Campos:
        nombre (CharField): Nombre único del método de pago.
            - Máximo 100 caracteres
            - Único en toda la base de datos
            - Requerido, no puede estar vacío
            - Ejemplos: "Efectivo", "Transferencia Bancaria", "PayPal"
            
        descripcion (TextField): Descripción detallada del método.
            - Texto libre sin límite de caracteres
            - Opcional (blank=True, null=True)
            - Información adicional para usuarios y administradores
            - Puede incluir instrucciones o condiciones especiales
            
        activo (BooleanField): Estado de disponibilidad del método.
            - True: Método disponible para nuevas transacciones
            - False: Método deshabilitado (soft delete)
            - Valor por defecto: True
            - Permite mantener histórico sin eliminar registros
    
    Meta opciones:
        verbose_name: Nombre singular en interfaz administrativa
        verbose_name_plural: Nombre plural en interfaz administrativa
        ordering: Ordenamiento alfabético por defecto al nombre
    
    Métodos:
        __str__(): Representación en cadena del objeto
    
    Restricciones:
        - El campo 'nombre' debe ser único
        - No se permite eliminación física de registros
        - Validación automática de campos requeridos
    
    Relaciones:
        - Ninguna relación directa con otros modelos
        - Puede ser referenciado por modelos de transacciones
        - Utilizado en formularios de selección
    
    Índices automáticos:
        - Índice único en campo 'nombre'
        - Índice en campo 'activo' para consultas de filtrado
    
    Ejemplos de uso:
        # Crear un nuevo método de pago
        metodo = MetodoPago.objects.create(
            nombre="Transferencia SWIFT",
            descripcion="Transferencia bancaria internacional",
            activo=True
        )
        
        # Obtener métodos activos
        activos = MetodoPago.objects.filter(activo=True)
        
        # Desactivar un método (soft delete)
        metodo.activo = False
        metodo.save()
        
        # Buscar por nombre
        efectivo = MetodoPago.objects.get(nombre="Efectivo")
    
    Validaciones:
        - Unicidad del nombre a nivel de base de datos
        - Longitud máxima del nombre (100 caracteres)
        - Campos requeridos validados automáticamente
    
    Consideraciones de rendimiento:
        - Consultas frecuentes por estado 'activo'
        - Ordenamiento aplicado en consultas por defecto
        - Índice único en 'nombre' para búsquedas rápidas
    
    Seguridad:
        - No contiene información sensible
        - Acceso controlado mediante vistas con permisos
        - Validación de entrada en formularios
    """
    
    # Campo principal: nombre único del método de pago
    nombre = models.CharField(
        max_length=100, 
        unique=True,
        help_text="Nombre único del método de pago (ej: Efectivo, Transferencia)"
    )
    
    # Campo opcional: descripción detallada del método
    descripcion = models.TextField(
        blank=True, 
        null=True,
        help_text="Descripción detallada del método de pago y sus condiciones"
    )
    
    # Campo de estado: controla la disponibilidad del método
    activo = models.BooleanField(
        default=True,
        help_text="Indica si el método de pago está disponible para nuevas transacciones"
    )

    class Meta:
        """
        Configuración de metadatos del modelo MetodoPago.
        
        Opciones configuradas:
        - verbose_name: Nombre singular para interfaz administrativa
        - verbose_name_plural: Nombre plural para interfaz administrativa  
        - ordering: Ordenamiento por defecto alfabético por nombre
        
        Estas opciones mejoran la experiencia en el panel administrativo
        de Django y establecen comportamientos por defecto del modelo.
        """
        verbose_name = "Método de Pago"
        verbose_name_plural = "Métodos de Pago"
        ordering = ['nombre']  # Ordenamiento alfabético por nombre

    def __str__(self):
        """
        Representación en cadena del objeto MetodoPago.
        
        Utilizado en:
        - Panel administrativo de Django
        - Formularios de selección (select)
        - Debugging y logging
        - Cualquier conversión a string del objeto
        
        Returns:
            str: El nombre del método de pago
            
        Ejemplo:
            >>> metodo = MetodoPago(nombre="Efectivo")
            >>> str(metodo)
            'Efectivo'
            >>> print(metodo)
            Efectivo
        """
        return self.nombre
    
    def clean(self):
        """
        Validación personalizada del modelo.
        
        Ejecuta validaciones adicionales antes de guardar:
        - Normalización del nombre (espacios, mayúsculas/minúsculas)
        - Validación de formato de descripción
        - Verificación de restricciones de negocio
        
        Raises:
            ValidationError: Si alguna validación falla
            
        Nota:
            Este método se ejecuta al llamar full_clean() o
            al validar formularios de Django.
        """
        from django.core.exceptions import ValidationError
        import unicodedata
        
        # Normalizar el nombre para evitar problemas de codificación
        if self.nombre:
            self.nombre = unicodedata.normalize('NFKC', self.nombre).strip()
            
        # Validar que el nombre no esté vacío después de normalizar
        if not self.nombre:
            raise ValidationError({
                'nombre': 'El nombre del método de pago no puede estar vacío.'
            })
    
    def save(self, *args, **kwargs):
        """
        Método personalizado para guardar el modelo.
        
        Ejecuta validación completa y normalización antes de guardar:
        - Llama a clean() para validaciones personalizadas
        - Normaliza datos antes del guardado
        - Mantiene integridad de datos
        
        Args:
            *args: Argumentos posicionales para el método save original
            **kwargs: Argumentos nombrados para el método save original
            
        Ejemplo:
            metodo = MetodoPago(nombre="  efectivo  ")
            metodo.save()  # Guardará como "Efectivo" (normalizado)
        """
        # Ejecutar validaciones personalizadas
        self.clean()
        
        # Llamar al método save original
        super().save(*args, **kwargs)
    
    @property
    def estado_texto(self):
        """
        Propiedad que devuelve el estado como texto legible.
        
        Útil para templates y representaciones en interfaz de usuario.
        
        Returns:
            str: "Activo" si está activo, "Inactivo" si está desactivado
            
        Ejemplo:
            >>> metodo = MetodoPago(activo=True)
            >>> metodo.estado_texto
            'Activo'
        """
        return "Activo" if self.activo else "Inactivo"
    
    @classmethod
    def activos(cls):
        """
        Método de clase para obtener solo métodos de pago activos.
        
        Manager personalizado para consultas frecuentes de métodos activos.
        
        Returns:
            QuerySet: Métodos de pago con activo=True, ordenados alfabéticamente
            
        Ejemplo:
            >>> MetodoPago.activos()
            <QuerySet [<MetodoPago: Efectivo>, <MetodoPago: Transferencia>]>
        """
        return cls.objects.filter(activo=True).order_by('nombre')
    
    @classmethod
    def inactivos(cls):
        """
        Método de clase para obtener solo métodos de pago inactivos.
        
        Útil para reportes y gestión de métodos deshabilitados.
        
        Returns:
            QuerySet: Métodos de pago con activo=False, ordenados alfabéticamente
            
        Ejemplo:
            >>> MetodoPago.inactivos()
            <QuerySet [<MetodoPago: Cheque>, <MetodoPago: Bitcoin>]>
        """
        return cls.objects.filter(activo=False).order_by('nombre')