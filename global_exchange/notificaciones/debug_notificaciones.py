import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "global_exchange.settings")
django.setup()

from decimal import Decimal
from cotizaciones.models import TasaDeCambio
from notificaciones.models import NotificacionMoneda
from monedas.models import Moneda
from django.contrib.auth import get_user_model

User = get_user_model()

print("\n" + "="*70)
print("🔍 DIAGNÓSTICO DEL SISTEMA DE NOTIFICACIONES")
print("="*70 + "\n")

# 1. Verificar que el signal está registrado
print("1️⃣ Verificando signals...")
from django.db.models import signals
receivers = signals.post_save.receivers
signal_count = len([r for r in receivers if 'notificar_cambio_tasa' in str(r)])
print(f"   Signals registrados para post_save: {signal_count}")
if signal_count > 0:
    print("   ✅ Signal está registrado")
else:
    print("   ❌ Signal NO está registrado - revisa apps.py")

# 2. Verificar configuraciones de usuario
print("\n2️⃣ Configuraciones de usuario:")
user = User.objects.get(id=2)  # Tu usuario
notificaciones = NotificacionMoneda.objects.filter(user=user, activa=True)
print(f"   Usuario: {user.username} (ID: {user.id})")
print(f"   Notificaciones activas: {notificaciones.count()}")
for n in notificaciones:
    print(f"      • {n.moneda.abreviacion} ({n.moneda.nombre})")

# 3. Verificar tasas existentes
print("\n3️⃣ Tasas de cambio disponibles:")
tasa = TasaDeCambio.objects.first()
if tasa:
    print(f"   Moneda origen: {tasa.moneda_origen.abreviacion}")
    print(f"   Moneda destino: {tasa.moneda_destino.abreviacion}")
    print(f"   Precio base actual: {tasa.precio_base}")
    
    # Verificar si el usuario tiene activa esta moneda
    tiene_activa = NotificacionMoneda.objects.filter(
        user=user,
        moneda=tasa.moneda_origen,
        activa=True
    ).exists()
    
    if tiene_activa:
        print(f"   ✅ Usuario tiene activa {tasa.moneda_origen.abreviacion}")
    else:
        print(f"   ❌ Usuario NO tiene activa {tasa.moneda_origen.abreviacion}")
        print(f"   💡 Necesitas activar {tasa.moneda_origen.abreviacion} en /notificaciones/")
else:
    print("   ❌ No hay tasas de cambio en la base de datos")

# 4. Verificar historial de tasas
print("\n4️⃣ Historial de tasas (para detectar cambios):")
if tasa:
    tasas_historicas = TasaDeCambio.objects.filter(
        moneda_origen=tasa.moneda_origen,
        moneda_destino=tasa.moneda_destino
    ).order_by('-fecha_actualizacion')[:3]
    
    print(f"   Total de registros: {tasas_historicas.count()}")
    for i, t in enumerate(tasas_historicas, 1):
        print(f"   {i}. ID:{t.id} - Precio: {t.precio_base} - Fecha: {t.fecha_actualizacion}")
    
    if tasas_historicas.count() < 2:
        print("   ⚠️ Solo hay 1 registro, el signal necesita al menos 2 para comparar")

# 5. Verificar Channel Layers
print("\n5️⃣ Verificando Channel Layers:")
from channels.layers import get_channel_layer
channel_layer = get_channel_layer()
print(f"   Backend: {channel_layer.__class__.__name__}")
print(f"   Configuración: {type(channel_layer).__name__}")

# 6. Test de envío manual
print("\n6️⃣ Test de envío manual:")
print("   Ejecutando envío de prueba...")

from asgiref.sync import async_to_sync

try:
    async_to_sync(channel_layer.group_send)(
        f"notificaciones_user_{user.id}",
        {
            'type': 'notificar_cambio_tasa',
            'moneda': 'USD',
            'precio_anterior': 7000.0,
            'precio_nuevo': 7350.0,
            'porcentaje_cambio': 5.0,
        }
    )
    print("   ✅ Envío manual exitoso")
    print("   💡 Si ves esto pero no aparece en el navegador, el problema está en el WebSocket")
except Exception as e:
    print(f"   ❌ Error al enviar: {e}")

print("\n" + "="*70)
print("\n💡 RECOMENDACIONES:")
print("   1. Asegúrate que el servidor Django está corriendo")
print("   2. Abre la página /notificaciones/ en el navegador")
print("   3. Revisa la consola del navegador (F12) para ver mensajes de WebSocket")
print("   4. Si usas Redis, verifica que esté corriendo: redis-cli ping")
print("\n" + "="*70 + "\n")