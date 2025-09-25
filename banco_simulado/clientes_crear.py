import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'banco_simulado.settings')
django.setup()

from transaccion.models import Cliente

# Datos de clientes de prueba
clientes_prueba = [
    {"email": "florentinlucas77@gmail.com", "nombre": "Lucas Vargas", "saldo": 1500000000.00},
    {"email": "maria@email.com", "nombre": "María García", "saldo": 2000000000.00},
    {"email": "carlos@email.com", "nombre": "Carlos López", "saldo": 800000000.00},
    {"email": "ana@email.com", "nombre": "Ana Martínez", "saldo": 1200000000.00},
    {"email": "admin@casacambios.com", "nombre": "Admin Casa Cambios", "saldo": 5000000000.00},
]

for cliente_data in clientes_prueba:
    cliente, created = Cliente.objects.get_or_create(
        email=cliente_data["email"],
        defaults={
            "nombre": cliente_data["nombre"],
            "saldo": cliente_data["saldo"]
        }
    )
    
    if created:
        print(f"✅ Cliente creado: {cliente.nombre} ({cliente.email}) - Saldo: ${cliente.saldo}")
    else:
        print(f"⚠️  Cliente ya existe: {cliente.nombre} ({cliente.email})")

print("\n🎉 Clientes de prueba creados exitosamente!")