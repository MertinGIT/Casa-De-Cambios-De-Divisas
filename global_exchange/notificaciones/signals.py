"""
Signals de la aplicación Notificaciones.

Este módulo se encarga de escuchar los cambios realizados en las tasas de cambio (TasaDeCambio)
y generar notificaciones en tiempo real hacia los usuarios suscritos a dichas monedas.

Incluye:
    - Captura de valores anteriores a una modificación (pre_save)
    - Registro de auditoría y detección de cambios significativos (post_save)
    - Envío de notificaciones mediante WebSockets (Channels)
"""
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from decimal import Decimal
from datetime import datetime
from cotizaciones.models import TasaDeCambio
from notificaciones.models import NotificacionMoneda, AuditoriaTasaCambio

UMBRAL_CAMBIO = Decimal('0.01')  # 1% de cambio mínimo

# Variable temporal para almacenar valores antes de guardar
_valores_anteriores = {}


@receiver(pre_save, sender=TasaDeCambio)
def capturar_valores_anteriores(sender, instance, **kwargs):
    """
    Captura los valores actuales de una tasa de cambio ANTES de ser guardada.

    Permite comparar los valores previos con los nuevos en la señal post_save
    para determinar si hubo cambios relevantes.
    """
    if instance.pk:  # Si existe, es una edición
        try:
            tasa_actual = TasaDeCambio.objects.get(pk=instance.pk)
            _valores_anteriores[instance.pk] = {
                'precio': tasa_actual.precio_base,
                'vigencia': tasa_actual.vigencia,
                'estado': tasa_actual.estado
            }
        except TasaDeCambio.DoesNotExist:
            pass


def notificar_tasa_mas_actual(moneda_origen, moneda_destino, tasa_editada_id=None):
    """
    Notifica a los usuarios cuando se detecta un cambio en la tasa más actual.

    - Compara la tasa más reciente con la inmediatamente anterior.
    - Si el cambio porcentual supera el umbral definido, envía una notificación
      por WebSocket a los usuarios que tengan activa la notificación de esa moneda.
    """
    # Buscar la tasa más actual
    tasa_mas_actual = TasaDeCambio.objects.filter(
        moneda_origen=moneda_origen,
        moneda_destino=moneda_destino,
        estado=True
    ).order_by('-vigencia').first()
    
    if not tasa_mas_actual:
        print("ℹ️ No hay tasas activas")
        return
    
    # Buscar la tasa anterior a la más actual
    tasa_anterior = TasaDeCambio.objects.filter(
        moneda_origen=moneda_origen,
        moneda_destino=moneda_destino,
        estado=True,
        vigencia__lt=tasa_mas_actual.vigencia
    ).order_by('-vigencia').first()
    
    if not tasa_anterior:
        print("ℹ️ No hay tasa anterior para comparar")
        return
    
    # Calcular cambio
    cambio = abs((tasa_mas_actual.precio_base - tasa_anterior.precio_base) / tasa_anterior.precio_base * 100)
    
    if cambio < UMBRAL_CAMBIO:
        print(f"ℹ️ Cambio menor al umbral ({cambio:.2f}%)")
        return
    
    # Obtener usuarios activos
    usuarios_activos = NotificacionMoneda.objects.filter(
        moneda=moneda_origen,
        activa=True
    ).select_related('user')
    
    if not usuarios_activos.exists():
        print("⚠️ No hay usuarios con notificaciones activas")
        return
    
    # Enviar notificaciones
    channel_layer = get_channel_layer()
    
    for notificacion in usuarios_activos:
        user = notificacion.user
        group_name = f"notificaciones_user_{user.id}"
        
        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                'type': 'notificar_cambio_tasa',
                'moneda': moneda_destino.abreviacion,
                'precio_anterior': float(tasa_anterior.precio_base),
                'precio_nuevo': float(tasa_mas_actual.precio_base),
                'porcentaje_cambio': float(cambio),
                'es_nueva': False,
                'tipo_cambio': 'CAMBIO_TASA_ACTUAL',
                'vigencia': tasa_mas_actual.vigencia.isoformat(),
                'timestamp': datetime.now().isoformat()
            }
        )
    
    print(f"✅ Cambio en tasa MÁS ACTUAL - Notificado a {usuarios_activos.count()} usuario(s)")
    print(f"   Tasa actual: {tasa_mas_actual.vigencia} (${tasa_mas_actual.precio_base})")
    print(f"   Tasa anterior: {tasa_anterior.vigencia} (${tasa_anterior.precio_base})")
    print(f"   Cambio: {cambio:.2f}%")


@receiver(post_save, sender=TasaDeCambio)
def notificar_cambio_tasa(sender, instance, created, **kwargs):
    """
    Maneja los eventos DESPUÉS de guardar una tasa de cambio (TasaDeCambio).

    Acciones:
        - Registra la operación en la tabla AuditoriaTasaCambio.
        - Determina si se debe notificar un cambio significativo.
        - Envía la notificación a los usuarios que tengan activadas alertas 
          para la moneda correspondiente.

    Casos tratados:
        1. Creación de una nueva tasa (CREACION)
        2. Edición de una tasa existente (EDICION)
        3. Detección de cambios de vigencia o pérdida de actualidad
        4. Evita notificar cambios menores al umbral
    """
    precio_anterior = None
    vigencia_anterior = None
    estado_anterior = None
    cambio_vigencia = False
    
    # Determinar tipo de cambio y valores anteriores
    if created:
        # 🔥 CREACIÓN
        tipo_cambio = 'CREACION'
        
        # Verificar si hay tasas con vigencia posterior
        existe_tasa_mas_reciente = TasaDeCambio.objects.filter(
            moneda_origen=instance.moneda_origen,
            moneda_destino=instance.moneda_destino,
            estado=True,
            vigencia__gt=instance.vigencia
        ).exclude(pk=instance.pk).exists()
        
        if existe_tasa_mas_reciente:
            print(f"⚠️ CREACIÓN de tasa histórica (vigencia: {instance.vigencia}). NO se notifica.")
            AuditoriaTasaCambio.objects.create(
                tasa=instance,
                tipo_cambio=tipo_cambio,
                precio_anterior=None,
                vigencia_anterior=None,
                estado_anterior=None,
                precio_nuevo=instance.precio_base,
                vigencia_nueva=instance.vigencia,
                estado_nuevo=instance.estado,
            )
            return
        
        # Es la más actual, buscar la anterior
        tasa_anterior = TasaDeCambio.objects.filter(
            moneda_origen=instance.moneda_origen,
            moneda_destino=instance.moneda_destino,
            estado=True,
            vigencia__lt=instance.vigencia
        ).order_by('-vigencia').first()
        
        if tasa_anterior:
            precio_anterior = tasa_anterior.precio_base
            vigencia_anterior = tasa_anterior.vigencia
            estado_anterior = tasa_anterior.estado
            print(f"📋 Nueva tasa MÁS ACTUAL. Comparando con vigencia {vigencia_anterior}: ${precio_anterior}")
        else:
            print(f"ℹ️ Primera tasa activa para {instance.moneda_origen.abreviacion}")
    
    else:
        # 🔥 EDICIÓN
        tipo_cambio = 'EDICION'
        valores_previos = _valores_anteriores.get(instance.pk, {})
        precio_anterior = valores_previos.get('precio')
        vigencia_anterior = valores_previos.get('vigencia')
        estado_anterior = valores_previos.get('estado')
        
        # Detectar si cambió la vigencia
        cambio_vigencia = vigencia_anterior != instance.vigencia
        
        # Verificar si ERA la más actual ANTES de editar
        era_la_mas_actual = False
        if vigencia_anterior:
            era_la_mas_actual = not TasaDeCambio.objects.filter(
                moneda_origen=instance.moneda_origen,
                moneda_destino=instance.moneda_destino,
                estado=True,
                vigencia__gt=vigencia_anterior
            ).exclude(pk=instance.pk).exists()
        
        # Verificar si ES la más actual DESPUÉS de editar
        es_la_mas_actual = not TasaDeCambio.objects.filter(
            moneda_origen=instance.moneda_origen,
            moneda_destino=instance.moneda_destino,
            estado=True,
            vigencia__gt=instance.vigencia
        ).exclude(pk=instance.pk).exists()
        
        print(f"📊 Edición: era_actual={era_la_mas_actual}, es_actual={es_la_mas_actual}, cambió_vigencia={cambio_vigencia}")
        
        # 🔥 CASO 1: Era la más actual y SIGUE siendo la más actual
        if era_la_mas_actual and es_la_mas_actual:
            print(f"✏️ Editando tasa que SIGUE siendo la MÁS ACTUAL")
            # Compara con su propio valor anterior
        
        # 🔥 CASO 2: NO era la más actual, pero AHORA SÍ lo es
        elif not era_la_mas_actual and es_la_mas_actual:
            print(f"✏️ Tasa que AHORA es la MÁS ACTUAL (vigencia cambió de {vigencia_anterior} a {instance.vigencia})")
            # Buscar la tasa que ERA la más actual antes de esta edición
            tasa_que_era_actual = TasaDeCambio.objects.filter(
                moneda_origen=instance.moneda_origen,
                moneda_destino=instance.moneda_destino,
                estado=True,
                vigencia__lt=instance.vigencia
            ).exclude(pk=instance.pk).order_by('-vigencia').first()
            
            if tasa_que_era_actual:
                precio_anterior = tasa_que_era_actual.precio_base
                vigencia_anterior = tasa_que_era_actual.vigencia
                print(f"📋 Comparando con la que ERA la más actual: {vigencia_anterior} (${precio_anterior})")
        
        # 🔥 CASO 3: Era la más actual pero YA NO lo es
        elif era_la_mas_actual and not es_la_mas_actual:
            print(f"⚠️ Tasa que ERA la más actual YA NO lo es (vigencia: {vigencia_anterior} → {instance.vigencia})")
            
            # Registrar en auditoría
            AuditoriaTasaCambio.objects.create(
                tasa=instance,
                tipo_cambio=tipo_cambio,
                precio_anterior=precio_anterior,
                vigencia_anterior=vigencia_anterior,
                estado_anterior=estado_anterior,
                precio_nuevo=instance.precio_base,
                vigencia_nueva=instance.vigencia,
                estado_nuevo=instance.estado,
            )
            
            if instance.pk in _valores_anteriores:
                del _valores_anteriores[instance.pk]
            
            # 🔥 Notificar sobre la que AHORA es la más actual
            notificar_tasa_mas_actual(instance.moneda_origen, instance.moneda_destino, instance.pk)
            return
        
        # 🔥 CASO 4: NO era ni ES la más actual
        else:
            print(f"⚠️ Tasa que NO es la más actual. NO se notifica.")
            AuditoriaTasaCambio.objects.create(
                tasa=instance,
                tipo_cambio=tipo_cambio,
                precio_anterior=precio_anterior,
                vigencia_anterior=vigencia_anterior,
                estado_anterior=estado_anterior,
                precio_nuevo=instance.precio_base,
                vigencia_nueva=instance.vigencia,
                estado_nuevo=instance.estado,
            )
            if instance.pk in _valores_anteriores:
                del _valores_anteriores[instance.pk]
            return
        
        if instance.pk in _valores_anteriores:
            del _valores_anteriores[instance.pk]
    
    # === REGISTRAR EN AUDITORÍA ===
    auditoria = AuditoriaTasaCambio.objects.create(
        tasa=instance,
        tipo_cambio=tipo_cambio,
        precio_anterior=precio_anterior,
        vigencia_anterior=vigencia_anterior,
        estado_anterior=estado_anterior,
        precio_nuevo=instance.precio_base,
        vigencia_nueva=instance.vigencia,
        estado_nuevo=instance.estado,
    )
    
    # Validaciones
    if not instance.estado:
        print(f"⚠️ Tasa inactiva, no se notifica")
        return
    
    if precio_anterior is None:
        print(f"ℹ️ No hay precio anterior para comparar")
        return
    
    # Obtener usuarios activos
    usuarios_activos = NotificacionMoneda.objects.filter(
        moneda=instance.moneda_origen,
        activa=True
    ).select_related('user')

    if not usuarios_activos.exists():
        print(f"⚠️ No hay usuarios con notificaciones activas")
        return

    # Calcular cambio
    cambio_precio = auditoria.porcentaje_cambio()
    
    # Notificar si hay cambio significativo O cambió vigencia
    debe_notificar = cambio_precio >= UMBRAL_CAMBIO or (cambio_vigencia and not created)
    
    if not debe_notificar:
        print(f"ℹ️ No hay cambio significativo (precio: {cambio_precio:.2f}%)")
        return

    # === ENVIAR NOTIFICACIONES ===
    channel_layer = get_channel_layer()

    for notificacion in usuarios_activos:
        user = notificacion.user
        group_name = f"notificaciones_user_{user.id}"
        
        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                'type': 'notificar_cambio_tasa',
                'moneda': instance.moneda_destino.abreviacion,
                'precio_anterior': float(precio_anterior),
                'precio_nuevo': float(instance.precio_base),
                'porcentaje_cambio': float(cambio_precio),
                'es_nueva': created,
                'tipo_cambio': tipo_cambio,
                'vigencia': instance.vigencia.isoformat(),
                'timestamp': datetime.now().isoformat()
            }
        )

    tipo_msg = "NUEVA tasa MÁS ACTUAL" if created else "EDICIÓN de tasa MÁS ACTUAL"
    print(f"✅ {tipo_msg} - Notificado a {usuarios_activos.count()} usuario(s)")
    print(f"   Vigencia: {vigencia_anterior} → {instance.vigencia}")
    print(f"   Precio: ${precio_anterior} → ${instance.precio_base} ({cambio_precio:.2f}%)")