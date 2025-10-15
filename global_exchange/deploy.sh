#!/bin/bash

echo "🚀 Desplegando Global Exchange en producción..."

# Detener y limpiar contenedores previos
echo "🧹 Limpiando contenedores anteriores..."
docker-compose -f docker-compose.prod.yml down

# Limpiar volumen de PostgreSQL si necesitas una instalación limpia
# Descomenta la siguiente línea si quieres reiniciar la base de datos
# docker volume rm $(docker volume ls -q | grep postgres_data) 2>/dev/null || true

# Construir y levantar servicios
echo "🔨 Construyendo servicios..."
docker-compose -f docker-compose.prod.yml build

echo "🚀 Levantando servicios..."
docker-compose -f docker-compose.prod.yml up -d

# Esperar a que los servicios estén listos
echo "⏳ Esperando a que los servicios estén listos..."
sleep 15

# Verificar estado de los contenedores
echo "📊 Estado de los contenedores:"
docker-compose -f docker-compose.prod.yml ps

# Verificar que db esté healthy
echo "🔍 Verificando salud de PostgreSQL..."
MAX_ATTEMPTS=30
ATTEMPT=0

until [ "$(docker-compose -f docker-compose.prod.yml ps db --format json | grep -o '"Health":"[^"]*"' | cut -d'"' -f4)" = "healthy" ] || [ $ATTEMPT -eq $MAX_ATTEMPTS ]; do
    ATTEMPT=$((ATTEMPT+1))
    echo "Esperando PostgreSQL... Intento $ATTEMPT/$MAX_ATTEMPTS"
    sleep 2
done

if [ $ATTEMPT -eq $MAX_ATTEMPTS ]; then
    echo "❌ Error: PostgreSQL no está saludable después de $MAX_ATTEMPTS intentos"
    echo "Logs de PostgreSQL:"
    docker-compose -f docker-compose.prod.yml logs db
    exit 1
fi

echo "✅ PostgreSQL está saludable"

# Configurar PostgreSQL para aceptar conexiones remotas
echo "🔧 Configurando PostgreSQL para conexiones remotas..."
chmod +x configure-postgres.sh 2>/dev/null || true
./configure-postgres.sh 2>/dev/null || {
    echo "⚠️  Script de configuración no encontrado, configurando manualmente..."
    
    # Configuración manual inline
    docker-compose -f docker-compose.prod.yml exec -T db bash -c "cat > /var/lib/postgresql/data/pg_hba.conf << 'EOF'
# TYPE  DATABASE        USER            ADDRESS                 METHOD
local   all             all                                     trust
host    all             all             127.0.0.1/32            trust
host    all             all             ::1/128                 trust
host    all             all             0.0.0.0/0               md5
host    all             all             192.168.0.0/16          md5
host    all             all             172.0.0.0/8             md5
EOF"
    
    docker-compose -f docker-compose.prod.yml exec -T db bash -c "su - postgres -c 'pg_ctl reload -D /var/lib/postgresql/data'"
    sleep 3
}

# Ejecutar migraciones
echo "🔄 Ejecutando migraciones..."
docker-compose -f docker-compose.prod.yml exec -T web python manage.py makemigrations
docker-compose -f docker-compose.prod.yml exec -T web python manage.py migrate

# Copiar archivos estáticos
echo "📦 Copiando archivos estáticos..."
docker-compose -f docker-compose.prod.yml exec -T web python manage.py collectstatic --noinput

# Verificar servicios
echo "📊 Estado final de servicios:"
docker-compose -f docker-compose.prod.yml ps

echo ""
echo "✅ Despliegue completado exitosamente!"
echo ""
echo "📌 URLs de acceso:"
echo "   - Aplicación web: http://192.168.100.168"
echo "   - Base de datos PostgreSQL:"
echo "     • Host: 192.168.100.168"
echo "     • Puerto: 5432"
echo "     • Base de datos: db_global_exchange"
echo "     • Usuario: postgres"
echo "     • Contraseña: 1234"
echo ""
echo "💡 Para conectar con DBeaver usa:"
echo "   jdbc:postgresql://192.168.100.168:5432/db_global_exchange"