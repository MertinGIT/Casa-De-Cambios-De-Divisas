from django.shortcuts import render
from django.utils import timezone
from django.db.models import Sum,Q,Count, Case, When, F, DecimalField
from decimal import Decimal
from datetime import timedelta
from operaciones.models import Transaccion
from clientes.models import Cliente
from monedas.models import Moneda

def admin_dashboard(request):
    # Fecha actual del servidor
    fecha_actual = timezone.localdate()
    hoy = timezone.localdate()
    ayer = hoy - timedelta(days=1)
    labels_7d, data_7d = obtener_ganancias_por_rango(7)
    labels_30d, data_30d = obtener_ganancias_por_rango(30)
    labels_3m, data_3m = obtener_ganancias_por_rango(90)

    # Ganancias hoy: suma de tasa_usada de transacciones confirmadas hoy
    ganancias_hoy = Transaccion.objects.filter(
        fecha__date=fecha_actual,
        estado="confirmada"
    ).aggregate(total=Sum('ganancia'))['total'] or Decimal('0.0')
    print("Ganancias hoy:", ganancias_hoy,flush=True)
    
    # Fecha de ayer
    fecha_ayer = fecha_actual - timedelta(days=1)
    # Ganancias ayer
    ganancias_ayer = Transaccion.objects.filter(
        fecha__date=fecha_ayer,
        estado="confirmada"
    ).aggregate(total=Sum('ganancia'))['total'] or Decimal('0.0')
    print("Ganancias ayer:", ganancias_ayer, flush=True)

    # Número de transacciones hoy
    transacciones_hoy = Transaccion.objects.filter(estado="confirmada",
        fecha__date=fecha_actual
    ).count()
    promedio_transacciones_dia = int(Transaccion.objects.filter(fecha__month=hoy.month).count() / hoy.day)
    

    # Clientes activos (estado activo)
    clientes_activos = Cliente.objects.filter(estado="activo").count()
    nuevos_clientes_mes = Cliente.objects.filter(estado="activo", creado_en__month=hoy.month).count()

    moneda_mas_operada = Transaccion.objects.filter(
        estado="confirmada",
        fecha__month=hoy.month
    ).values("moneda_destino__abreviacion").annotate(total=Count("id")).order_by("-total").first()
    
    if moneda_mas_operada:
        moneda = moneda_mas_operada['moneda_destino__abreviacion']
        total_operaciones = moneda_mas_operada['total']
    else:
        moneda = None
        total_operaciones = 0
        
    
    print("Moneda más operada este mes:", moneda_mas_operada, flush=True)
    # Últimas transacciones
    ultimas_transacciones = Transaccion.ultimas(limite=5)
    
    top_monedas = (
    Transaccion.objects
    .filter(estado="confirmada",fecha__date=hoy)
    .values('moneda_origen__abreviacion', 'moneda_origen__nombre','moneda_destino__abreviacion', 'moneda_destino__nombre')
    .annotate(
        total=Count('id'),
        compras=Count('id', filter=Q(tipo='compra')),
        ventas=Count('id', filter=Q(tipo='venta'))
    )
    .order_by('-total')[:4]
)
    print("Top monedas hoy:", top_monedas, flush=True)

    context = {
        'fecha_actual': fecha_actual,
        'ganancias_hoy': ganancias_hoy,
        'ganancias_ayer': ganancias_ayer,
        'transacciones_hoy': transacciones_hoy,
        "promedio_transacciones_dia": promedio_transacciones_dia,
        'clientes_activos': clientes_activos,
        'nuevos_clientes_mes': nuevos_clientes_mes,
        'moneda_mas_operada':moneda,
        'total_operaciones': total_operaciones,
        'ultimas_transacciones': ultimas_transacciones,
         # Gráfico dinámico
        "labels_7d": labels_7d,
        "data_7d": data_7d,
        "labels_30d": labels_30d,
        "data_30d": data_30d,
        "labels_3m": labels_3m,
        "data_3m": data_3m,
        "top_monedas": top_monedas
    }

    return render(request, 'dashboard.html', context)

def obtener_ganancias_por_rango(dias_hacia_atras):
    """
    Retorna dos listas: labels (día/mes) y datos de ganancias (float)
    para los últimos `dias_hacia_atras` días.
    """
    hoy = timezone.localdate()
    dias = [hoy - timedelta(days=i) for i in range(dias_hacia_atras-1, -1, -1)]
    labels = [d.strftime("%d/%m") for d in dias]

    data = []
    for dia in dias:
        total = Transaccion.objects.filter(
            fecha__date=dia,
            estado="confirmada"
        ).aggregate(total=Sum('ganancia'))['total'] or 0
        data.append(float(total))

    return labels, data