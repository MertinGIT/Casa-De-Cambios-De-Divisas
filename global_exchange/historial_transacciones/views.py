from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.db.models import Q
from django.utils.dateparse import parse_date
from django.utils import timezone
from django.utils.dateparse import parse_date

@login_required
def historial_usuario(request):
    from operaciones.models import Transaccion
    from monedas.models import Moneda

    q = request.GET.get('q', '').strip()
    campo = request.GET.get('campo', '').strip()          # '', 'id', 'estado', 'tipo'
    moneda = request.GET.get('moneda', '').strip()        # abreviación
    fecha_inicio = request.GET.get('fecha_inicio', '').strip()
    fecha_fin = request.GET.get('fecha_fin', '').strip()

    transacciones = Transaccion.objects.filter(usuario=request.user).select_related(
        'moneda_origen', 'moneda_destino'
    )

    # Filtro moneda (si aparece en origen o destino)
    if moneda:
        transacciones = transacciones.filter(
            models.Q(moneda_origen__abreviacion=moneda) |
            models.Q(moneda_destino__abreviacion=moneda)
        )

    # Filtro fechas (fecha__date)
    if fecha_inicio:
        fi = parse_date(fecha_inicio)
        if fi:
            transacciones = transacciones.filter(fecha__date__gte=fi)
    if fecha_fin:
        ff = parse_date(fecha_fin)
        if ff:
            transacciones = transacciones.filter(fecha__date__lte=ff)

    # Búsqueda
    if q:
        if campo == 'id' or campo == '':
            if q.isdigit():
                transacciones = transacciones.filter(id=int(q))
            else:
                # fallback a búsqueda amplia si no es número
                transacciones = transacciones.filter(
                    models.Q(estado__icontains=q) |
                    models.Q(tipo__icontains=q)
                )
        elif campo == 'estado':
            transacciones = transacciones.filter(estado__icontains=q)
        elif campo == 'tipo':
            transacciones = transacciones.filter(tipo__icontains=q)
        else:
            transacciones = transacciones.filter(
                models.Q(id__icontains=q) |
                models.Q(estado__icontains=q) |
                models.Q(tipo__icontains=q)
            )

    transacciones = transacciones.order_by('-fecha')

    # Monedas disponibles (abreviaciones únicas presentes en las transacciones del usuario)
    monedas_set = set()
    for t in Transaccion.objects.filter(usuario=request.user).select_related('moneda_origen', 'moneda_destino'):
        if t.moneda_origen:
            monedas_set.add(t.moneda_origen.abreviacion)
        if t.moneda_destino:
            monedas_set.add(t.moneda_destino.abreviacion)
    monedas_disponibles = sorted(monedas_set)

    context = {
        'transacciones': transacciones,
        'q': q,
        'campo': campo,
        'moneda_sel': moneda,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'monedas_disponibles': monedas_disponibles,
    }
    return render(request, 'historial_transacciones/historial_usuario.html', context)

@login_required
def detalle_transaccion(request, transaccion_id):
    from operaciones.models import Transaccion
    transaccion = get_object_or_404(Transaccion, id=transaccion_id, usuario=request.user)
    return render(request, 'historial_transacciones/detalle_transaccion.html', {
        'transaccion': transaccion
    })

@login_required
def exportar_historial_excel(request):
    try:
        import openpyxl
        from openpyxl.utils import get_column_letter
    except ImportError:
        return JsonResponse({'error': 'Instalar openpyxl'}, status=500)

    from operaciones.models import Transaccion
    qs = Transaccion.objects.filter(usuario=request.user).order_by('-fecha')

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Historial"

    headers = ["ID", "Fecha", "Monto", "Moneda Origen", "Moneda Destino", "Tipo", "Tasa Usada", "Estado"]
    ws.append(headers)

    for t in qs:
        ws.append([
            t.id,
            timezone.localtime(t.fecha).strftime('%d/%m/%Y %H:%M') if t.fecha else '',
            float(t.monto) if getattr(t, 'monto', None) is not None else 0,
            t.moneda_origen.abreviacion if t.moneda_origen else '',
            t.moneda_destino.abreviacion if t.moneda_destino else '',
            t.tipo,
            t.tasa_usada if getattr(t, 'tasa_usada', None) is not None else '',
            t.estado,
            
        ])

    for col in range(1, len(headers) + 1):
        ws.column_dimensions[get_column_letter(col)].width = 18

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename=historial_transacciones.xlsx'
    wb.save(response)
    return response

@login_required
def exportar_historial_pdf(request):
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
        from reportlab.lib import colors
    except ImportError:
        return JsonResponse({'error': 'Instalar reportlab'}, status=500)

    from operaciones.models import Transaccion
    qs = Transaccion.objects.filter(usuario=request.user).order_by('-fecha')

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=historial_transacciones.pdf'

    p = canvas.Canvas(response, pagesize=A4)
    width, height = A4
    y = height - 50

    # Título
    p.setFont("Helvetica-Bold", 14)
    p.drawString(40, y, "Historial de Transacciones")
    y -= 30

    # Encabezados (los mismos que en Excel)
    headers = ["ID", "Fecha", "Monto", "Moneda Origen", "Moneda Destino", "Tipo", "Tasa Usada", "Estado"]
    p.setFont("Helvetica-Bold", 9)

    # Posiciones X (ajustadas para A4 horizontalmente)
    x_positions = [40, 80, 150, 220, 300, 380, 450, 520]

    for x, h in zip(x_positions, headers):
        p.drawString(x, y, h)
    y -= 12
    p.setLineWidth(0.5)
    p.line(40, y, width - 40, y)
    y -= 10

    # Filas de datos
    p.setFont("Helvetica", 8)
    for t in qs:
        if y < 60:  # salto de página
            p.showPage()
            y = height - 50
            p.setFont("Helvetica-Bold", 9)
            for x, h in zip(x_positions, headers):
                p.drawString(x, y, h)
            y -= 22
            p.setFont("Helvetica", 8)

        valores = [
            str(t.id),
            timezone.localtime(t.fecha).strftime('%d/%m/%Y %H:%M') if t.fecha else '',
            str(int(t.monto)) if getattr(t, 'monto', None) is not None else '0',
            t.moneda_origen.abreviacion if t.moneda_origen else '',
            t.moneda_destino.abreviacion if t.moneda_destino else '',
            t.tipo,
            str(int(t.tasa_usada)) if getattr(t, 'tasa_usada', None) is not None else '',
            t.estado,
        ]

        for x, v in zip(x_positions, valores):
            p.drawString(x, y, str(v))

        y -= 14

    p.showPage()
    p.save()
    return response