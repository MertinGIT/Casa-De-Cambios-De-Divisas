from django.db.models.signals import post_save
from django.dispatch import receiver
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from decimal import Decimal
from datetime import datetime
from cotizaciones.models import TasaDeCambio
from notificaciones.models import AuditoriaTasaCambio, NotificacionMoneda
from django.db.models.signals import post_save, pre_save

UMBRAL_CAMBIO = Decimal('0.01')  # 1% de cambio mínimo

# Variable temporal para almacenar valores antes de guardar
_valores_anteriores = {}

@receiver(pre_save, sender=TasaDeCambio)
def capturar_valores_anteriores(sender, instance, **kwargs):
    """
    ANTES de guardar, captura los valores actuales si es una edición.
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


@receiver(pre_save, sender=TasaDeCambio)
def capturar_valores_anteriores(sender, instance, **kwargs):
    """
    ANTES de guardar, captura los valores actuales si es una edición.
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


@receiver(post_save, sender=TasaDeCambio)
def notificar_cambio_tasa(sender, instance, created, **kwargs):
    """
    DESPUÉS de guardar, registra en auditoría y notifica cambios.
    """
    precio_anterior = None
    vigencia_anterior = None
    estado_anterior = None
    cambio_vigencia = False
    
    # Determinar tipo de cambio y valores anteriores
    if created:
        tipo_cambio = 'CREACION'
        
        # 🔥 VALIDACIÓN: ¿Hay tasas con vigencia POSTERIOR a la nueva?
        # Si hay tasas más recientes, esta es una tasa histórica y NO debe notificar
        existe_tasa_mas_reciente = TasaDeCambio.objects.filter(
            moneda_origen=instance.moneda_origen,
            moneda_destino=instance.moneda_destino,
            estado=True,
            vigencia__gt=instance.vigencia  # 🔥 Vigencias POSTERIORES
        ).exclude(pk=instance.pk).exists()
        
        if existe_tasa_mas_reciente:
            print(f"⚠️ CREACIÓN de tasa histórica (vigencia: {instance.vigencia}). Hay tasas más recientes. NO se notifica.")
            # 🔥 Registra en auditoría pero NO notifica
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
            return  # 🔥 SALIR sin notificar
        
        # 🔹 Si llegamos aquí, es la tasa MÁS ACTUAL
        # Buscar la tasa con vigencia más reciente ANTERIOR a esta
        ultima_auditoria = AuditoriaTasaCambio.objects.filter(
            tasa__moneda_origen=instance.moneda_origen,
            tasa__moneda_destino=instance.moneda_destino,
            tasa__estado=True,
            estado_nuevo=True,
            vigencia_nueva__lt=instance.vigencia
        ).order_by('-vigencia_nueva').first()
        
        if ultima_auditoria:
            precio_anterior = ultima_auditoria.precio_nuevo
            vigencia_anterior = ultima_auditoria.vigencia_nueva
            estado_anterior = ultima_auditoria.estado_nuevo
            print(f"📋 Nueva tasa MÁS ACTUAL. Comparando con auditoría de vigencia {vigencia_anterior}: {precio_anterior}")
        else:
            # Si no hay auditoría, buscar directamente en TasaDeCambio
            tasa_anterior = TasaDeCambio.objects.filter(
                moneda_origen=instance.moneda_origen,
                moneda_destino=instance.moneda_destino,
                estado=True,
                vigencia__lt=instance.vigencia
            ).exclude(pk=instance.pk).order_by('-vigencia').first()
            
            if tasa_anterior:
                precio_anterior = tasa_anterior.precio_base
                vigencia_anterior = tasa_anterior.vigencia
                estado_anterior = tasa_anterior.estado
                print(f"📋 Nueva tasa MÁS ACTUAL. Comparando con tasa de vigencia {vigencia_anterior}: {precio_anterior}")
            else:
                print(f"ℹ️ Primera tasa ACTIVA registrada para {instance.moneda_origen.abreviacion}")
    else:
        # 🔥 EDICIÓN
        tipo_cambio = 'EDICION'
        valores_previos = _valores_anteriores.get(instance.pk, {})
        precio_anterior = valores_previos.get('precio')
        vigencia_anterior = valores_previos.get('vigencia')
        estado_anterior = valores_previos.get('estado')
        
        # 🔥 DETECTAR SI CAMBIÓ LA VIGENCIA
        cambio_vigencia = vigencia_anterior != instance.vigencia
        
        if cambio_vigencia:
            print(f"📅 Cambió la vigencia: {vigencia_anterior} → {instance.vigencia}")
        
        # 🔥 VALIDACIÓN: ¿Hay tasas con vigencia POSTERIOR a la NUEVA vigencia?
        existe_tasa_mas_reciente = TasaDeCambio.objects.filter(
            moneda_origen=instance.moneda_origen,
            moneda_destino=instance.moneda_destino,
            estado=True,
            vigencia__gt=instance.vigencia  # 🔥 Comparar con la NUEVA vigencia
        ).exclude(pk=instance.pk).exists()
        
        if existe_tasa_mas_reciente:
            print(f"⚠️ EDICIÓN de tasa antigua (vigencia: {instance.vigencia}). Hay tasas más recientes. NO se notifica.")
            # 🔥 Registra en auditoría pero NO notifica
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
            # Limpiar valores anteriores
            if instance.pk in _valores_anteriores:
                del _valores_anteriores[instance.pk]
            return  # 🔥 SALIR sin notificar
        
        # 🔥 Si cambió la vigencia a una más actual, buscar con qué comparar
        if cambio_vigencia:
            print(f"✏️ Editando vigencia a la MÁS ACTUAL: {vigencia_anterior} → {instance.vigencia}")
            
            # Buscar la tasa con vigencia más reciente ANTERIOR a la nueva vigencia
            tasa_comparacion = TasaDeCambio.objects.filter(
                moneda_origen=instance.moneda_origen,
                moneda_destino=instance.moneda_destino,
                estado=True,
                vigencia__lt=instance.vigencia  # 🔥 Menor a la NUEVA vigencia
            ).exclude(pk=instance.pk).order_by('-vigencia').first()
            
            if tasa_comparacion:
                # 🔥 Comparar con la tasa más reciente anterior
                precio_anterior = tasa_comparacion.precio_base
                vigencia_anterior = tasa_comparacion.vigencia
                print(f"📋 Comparando con tasa anterior de vigencia {vigencia_anterior}: {precio_anterior}")
            else:
                print(f"⚠️ No hay tasa anterior para comparar")
        else:
            print(f"✏️ Editando precio de tasa MÁS ACTUAL: {precio_anterior} → {instance.precio_base} (vigencia: {instance.vigencia})")
        
        # Limpiar valores anteriores
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
    
    # 🔥 NO NOTIFICAR SI LA TASA NUEVA ESTÁ INACTIVA
    if not instance.estado:
        print(f"⚠️ Tasa inactiva, no se notifica")
        return
    
    # === NOTIFICAR SOLO SI HAY CAMBIO SIGNIFICATIVO ===
    # Si no hay precio anterior, no hay con qué comparar
    if precio_anterior is None:
        print(f"ℹ️ No hay precio anterior para comparar")
        return
    
    # Obtener usuarios con notificaciones activas
    usuarios_activos = NotificacionMoneda.objects.filter(
        moneda=instance.moneda_origen,
        activa=True
    ).select_related('user')

    if not usuarios_activos.exists():
        print(f"⚠️ No hay usuarios con notificaciones activas para {instance.moneda_origen.abreviacion}")
        return

    # 🔥 Calcular cambio porcentual
    cambio_precio = auditoria.porcentaje_cambio()
    
    # 🔥 NOTIFICAR SI:
    # 1. Hay cambio de precio significativo, O
    # 2. Cambió la vigencia a una fecha más actual (aunque el precio sea igual)
    debe_notificar = cambio_precio >= UMBRAL_CAMBIO or cambio_vigencia
    
    if not debe_notificar:
        print(f"ℹ️ No hay cambio significativo (precio: {cambio_precio:.2f}%, vigencia: {'cambió' if cambio_vigencia else 'sin cambio'})")
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
                'cambio_vigencia': cambio_vigencia,
                'timestamp': datetime.now().isoformat()
            }
        )

    if cambio_vigencia and cambio_precio < UMBRAL_CAMBIO:
        razon = "cambio de vigencia a fecha más actual"
    elif cambio_precio >= UMBRAL_CAMBIO:
        razon = f"cambio de precio ({cambio_precio:.2f}%)"
    else:
        razon = f"cambio de vigencia Y precio ({cambio_precio:.2f}%)"
    
    tipo = "NUEVA tasa MÁS ACTUAL" if created else f"EDICIÓN"
    print(f"✅ {tipo} - Notificado a {usuarios_activos.count()} usuario(s) para {instance.moneda_origen.abreviacion}")
    print(f"   Razón: {razon}")
    
    if created:
        print(f"   Vigencia anterior: {vigencia_anterior} (${precio_anterior}) → Vigencia nueva: {instance.vigencia} (${instance.precio_base})")
    else:
        print(f"   Vigencia: {vigencia_anterior} → {instance.vigencia} | Precio: ${precio_anterior} → ${instance.precio_base}")