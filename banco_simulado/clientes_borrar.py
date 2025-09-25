import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'banco_simulado.settings')
django.setup()

from transaccion.models import Cliente, Transaccion

def borrar_todos_los_clientes():
    """Borra todos los clientes y sus transacciones"""
    print("🗑️  Borrando todos los clientes...")
    
    # Contar antes de borrar
    total_clientes = Cliente.objects.count()
    total_transacciones = Transaccion.objects.count()
    
    print(f"📊 Clientes en BD: {total_clientes}")
    print(f"📊 Transacciones en BD: {total_transacciones}")
    
    if total_clientes == 0:
        print("ℹ️  No hay clientes para borrar.")
        return
    
    # Confirmar borrado
    respuesta = input(f"\n❓ ¿Estás seguro de borrar {total_clientes} clientes y {total_transacciones} transacciones? (s/N): ")
    
    if respuesta.lower() in ['s', 'si', 'sí', 'y', 'yes']:
        # Primero borrar transacciones (por foreign key)
        transacciones_borradas = Transaccion.objects.all().delete()[0]
        print(f"🗑️  Transacciones borradas: {transacciones_borradas}")
        
        # Luego borrar clientes
        clientes_borrados = Cliente.objects.all().delete()[0]
        print(f"🗑️  Clientes borrados: {clientes_borrados}")
        
        print("✅ Todos los clientes y transacciones han sido borrados exitosamente!")
    else:
        print("❌ Operación cancelada.")

def borrar_clientes_especificos():
    """Borra clientes específicos por email"""
    emails_a_borrar = [
        "juan@email.com",
        "maria@email.com", 
        "carlos@email.com",
        "ana@email.com",
        "admin@casacambios.com"
    ]
    
    print("🗑️  Borrando clientes específicos...")
    
    for email in emails_a_borrar:
        try:
            cliente = Cliente.objects.get(email=email)
            
            # Contar transacciones del cliente
            transacciones_count = Transaccion.objects.filter(email=email).count()
            
            # Borrar transacciones del cliente primero
            if transacciones_count > 0:
                Transaccion.objects.filter(email=email).delete()
                print(f"🗑️  Borradas {transacciones_count} transacciones de {email}")
            
            # Borrar cliente
            cliente.delete()
            print(f"✅ Cliente borrado: {cliente.nombre} ({email})")
            
        except Cliente.DoesNotExist:
            print(f"⚠️  Cliente no encontrado: {email}")

def listar_clientes():
    """Lista todos los clientes existentes"""
    clientes = Cliente.objects.all()
    
    if clientes.exists():
        print("\n📋 Clientes en la base de datos:")
        print("-" * 60)
        for cliente in clientes:
            transacciones_count = Transaccion.objects.filter(email=cliente.email).count()
            print(f"📧 {cliente.email}")
            print(f"👤 {cliente.nombre}")
            print(f"💰 ${cliente.saldo:,.2f}")
            print(f"📊 {transacciones_count} transacciones")
            print("-" * 60)
    else:
        print("ℹ️  No hay clientes en la base de datos.")

def menu():
    """Menú interactivo"""
    while True:
        print("\n" + "="*50)
        print("🏦 GESTIÓN DE CLIENTES - BANCO SIMULADO")
        print("="*50)
        print("1. 📋 Listar todos los clientes")
        print("2. 🗑️  Borrar clientes específicos")
        print("3. 💥 Borrar TODOS los clientes")
        print("4. 🚪 Salir")
        print("-"*50)
        
        opcion = input("Selecciona una opción (1-4): ").strip()
        
        if opcion == "1":
            listar_clientes()
        elif opcion == "2":
            borrar_clientes_especificos()
        elif opcion == "3":
            borrar_todos_los_clientes()
        elif opcion == "4":
            print("👋 ¡Hasta luego!")
            break
        else:
            print("❌ Opción inválida. Por favor selecciona 1, 2, 3 o 4.")

if __name__ == "__main__":
    menu()