from django.shortcuts import render

def simulador_operaciones(request):
    monedas = [
        {"abreviacion": "USD", "nombre": "Dólar estadounidense"},
        {"abreviacion": "EUR", "nombre": "Euro"},
        {"abreviacion": "PYG", "nombre": "Guaraní paraguayo"},
    ]

    transacciones = [
        {"id": 101, "fecha": "2025-09-15 14:30", "monto": "1,200 USD", "estado": "Completada", "tipo": "Compra"},
        {"id": 102, "fecha": "2025-09-14 09:10", "monto": "850 EUR", "estado": "Pendiente", "tipo": "Venta"},
        {"id": 103, "fecha": "2025-09-13 18:45", "monto": "5,000 PYG", "estado": "Cancelada", "tipo": "Compra"},
        {"id": 104, "fecha": "2025-09-12 11:20", "monto": "3,300 USD", "estado": "Completada", "tipo": "Venta"},
        {"id": 105, "fecha": "2025-09-11 16:05", "monto": "2,150 EUR", "estado": "Completada", "tipo": "Compra"},
    ]

    return render(request, "operaciones/conversorReal.html", {
        "monedas": monedas,
        "transacciones": transacciones,
    })
