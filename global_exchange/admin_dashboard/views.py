from django.shortcuts import render
from django.utils import timezone
from django.db.models import Sum,Q,Count, Case, When, F, DecimalField,Max
from decimal import Decimal
from datetime import timedelta,date
from operaciones.models import Transaccion
from clientes.models import Cliente
from monedas.models import Moneda
from cotizaciones.models import TasaDeCambio

def admin_dashboard(request):
    # Fechas
    fecha_actual = timezone.localdate()
    hoy = timezone.localdate()
    ayer = hoy - timedelta(days=1)
    
    # Obtener parámetros de filtro
    fecha_inicio_param = request.GET.get('fecha_inicio')
    fecha_fin_param = request.GET.get('fecha_fin')
    moneda_filtro = request.GET.get('moneda', 'todas')
    
    # Establecer rango por defecto (90 días)
    if fecha_inicio_param and fecha_fin_param:
        fecha_inicio = date.fromisoformat(fecha_inicio_param)
        fecha_fin = date.fromisoformat(fecha_fin_param)
    else:
        fecha_fin = hoy
        fecha_inicio = hoy - timedelta(days=90)
    
    # Stats básicos (SIN CAMBIOS - siempre del día actual)
    ganancias_hoy = Transaccion.objects.filter(
        fecha__date=fecha_actual,
        estado="confirmada"
    ).aggregate(total=Sum('ganancia'))['total'] or Decimal('0.0')
    
    ganancias_ayer = Transaccion.objects.filter(
        fecha__date=ayer,
        estado="confirmada"
    ).aggregate(total=Sum('ganancia'))['total'] or Decimal('0.0')
    
    transacciones_hoy = Transaccion.objects.filter(
        estado="confirmada",
        fecha__date=fecha_actual
    ).count()
    
    promedio_transacciones_dia = int(
        Transaccion.objects.filter(fecha__month=hoy.month).count() / hoy.day
    ) if hoy.day > 0 else 0
    
    clientes_activos = Cliente.objects.filter(estado="activo").count()
    nuevos_clientes_mes = Cliente.objects.filter(
        estado="activo", 
        creado_en__month=hoy.month
    ).count()
    
    moneda_mas_operada_data = Transaccion.objects.filter(
        estado="confirmada",
        fecha__month=hoy.month
    ).values("moneda_destino__abreviacion").annotate(
        total=Count("id")
    ).order_by("-total").first()
    
    moneda_mas_operada = moneda_mas_operada_data['moneda_destino__abreviacion'] if moneda_mas_operada_data else 'N/A'
    total_operaciones = moneda_mas_operada_data['total'] if moneda_mas_operada_data else 0
    
    # Top monedas del día (SIN CAMBIOS)
    top_monedas = (
        Transaccion.objects
        .filter(estado="confirmada", fecha__date=hoy)
        .values('moneda_destino__abreviacion', 'moneda_destino__nombre')
        .annotate(
            total=Count('id'),
            compras=Count('id', filter=Q(tipo='compra')),
            ventas=Count('id', filter=Q(tipo='venta'))
        )
        .order_by('-total')[:4]
    )
    
    # ✅ CORREGIDO: Últimas 5 transacciones confirmadas
    ultimas_transacciones = Transaccion.objects.filter(
        estado="confirmada"
    ).order_by('-fecha')[:5]
    
    # ✅ NUEVO: Calcular ganancia total del rango filtrado
    query_ganancia_rango = Transaccion.objects.filter(
        fecha__date__gte=fecha_inicio,
        fecha__date__lte=fecha_fin,
        estado="confirmada"
    )
    
    if moneda_filtro != 'todas':
        query_ganancia_rango = query_ganancia_rango.filter(
            Q(moneda_origen__abreviacion=moneda_filtro) | 
            Q(moneda_destino__abreviacion=moneda_filtro)
        )
    
    ganancia_total_rango = query_ganancia_rango.aggregate(
        total=Sum('ganancia')
    )['total'] or Decimal('0.0')
    
    # === GRÁFICOS CON FILTROS ===
    
    # 1. Ganancias por Fecha (con filtros aplicados)
    labels_ganancias_fecha = []
    data_ganancias_fecha = []
    ganancia_acumulada = Decimal('0.0')
    
    dias_rango = (fecha_fin - fecha_inicio).days + 1
    for i in range(dias_rango):
        dia = fecha_inicio + timedelta(days=i)
        labels_ganancias_fecha.append(dia.strftime("%d/%m"))
        
        query = Transaccion.objects.filter(
            fecha__date=dia,
            estado="confirmada"
        )
        
        if moneda_filtro != 'todas':
            query = query.filter(
                Q(moneda_origen__abreviacion=moneda_filtro) | 
                Q(moneda_destino__abreviacion=moneda_filtro)
            )
        
        ganancia = query.aggregate(total=Sum('ganancia'))['total'] or Decimal('0.0')
        data_ganancias_fecha.append(float(ganancia))
        ganancia_acumulada += ganancia
    
    # 2. Ganancias por Divisa (rango filtrado)
    ganancias_por_moneda_query = Transaccion.objects.filter(
        fecha__date__gte=fecha_inicio,
        fecha__date__lte=fecha_fin,
        estado="confirmada"
    )
    
    if moneda_filtro != 'todas':
        ganancias_por_moneda_query = ganancias_por_moneda_query.filter(
            Q(moneda_origen__abreviacion=moneda_filtro) | 
            Q(moneda_destino__abreviacion=moneda_filtro)
        )
    
    ganancias_por_moneda = (
        ganancias_por_moneda_query
        .values('moneda_destino__abreviacion')
        .annotate(total_ganancia=Sum('ganancia'))
        .order_by('-total_ganancia')[:5]
    )
    
    labels_ganancias_moneda = [m['moneda_destino__abreviacion'] for m in ganancias_por_moneda]
    data_ganancias_moneda = [float(m['total_ganancia']) for m in ganancias_por_moneda]
    
    # 3. Evolución de Tasas de Cambio (últimas tasas por día)
    monedas_disponibles = Moneda.objects.filter(estado=True).exclude(abreviacion='PYG')
    
    tasas_evolucion = {}
    for moneda in monedas_disponibles:
        # Obtener todas las fechas únicas con tasas en el rango
        fechas_con_tasas = (
            TasaDeCambio.objects
            .filter(
                moneda_destino=moneda,
                moneda_origen__abreviacion='PYG',
                vigencia__date__gte=fecha_inicio,
                vigencia__date__lte=fecha_fin,
                estado=True
            )
            .values('vigencia__date')
            .distinct()
            .order_by('vigencia__date')
        )
        
        labels_tasas = []
        data_compra = []
        data_venta = []
        
        for fecha_data in fechas_con_tasas:
            dia = fecha_data['vigencia__date']
            
            # Obtener la ÚLTIMA tasa del día
            ultima_tasa = (
                TasaDeCambio.objects
                .filter(
                    moneda_destino=moneda,
                    moneda_origen__abreviacion='PYG',
                    vigencia__date=dia,
                    estado=True
                )
                .order_by('-vigencia')
                .first()
            )
            
            if ultima_tasa:
                labels_tasas.append(dia.strftime("%d/%m"))
                data_compra.append(float(ultima_tasa.monto_compra))
                data_venta.append(float(ultima_tasa.monto_venta))
        
        tasas_evolucion[moneda.abreviacion] = {
            'labels': labels_tasas,
            'compra': data_compra,
            'venta': data_venta
        }
    
    context = {
        'fecha_actual': fecha_actual,
        'fecha_90_dias_atras': fecha_inicio,
        
        # ✅ NUEVO: Pasar valores de filtros para mantenerlos en el template
        'fecha_inicio_filtro': fecha_inicio,
        'fecha_fin_filtro': fecha_fin,
        'moneda_filtro': moneda_filtro,
        
        # Stats del día (sin cambios)
        'ganancias_hoy': ganancias_hoy,
        'ganancias_ayer': ganancias_ayer,
        'transacciones_hoy': transacciones_hoy,
        'promedio_transacciones_dia': promedio_transacciones_dia,
        'clientes_activos': clientes_activos,
        'nuevos_clientes_mes': nuevos_clientes_mes,
        'moneda_mas_operada': moneda_mas_operada,
        'total_operaciones': total_operaciones,
        
        # ✅ NUEVO: Ganancia total del rango filtrado
        'ganancia_total_rango': ganancia_total_rango,
        'dias_rango': dias_rango,
        
        'ultimas_transacciones': ultimas_transacciones,
        'top_monedas': top_monedas,
        'monedas_disponibles': monedas_disponibles,
        
        # Datos para gráficos (JSON serialized)
        'labels_ganancias_fecha': labels_ganancias_fecha,
        'data_ganancias_fecha': data_ganancias_fecha,
        'labels_ganancias_moneda': labels_ganancias_moneda,
        'data_ganancias_moneda': data_ganancias_moneda,
        'tasas_evolucion': tasas_evolucion,
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