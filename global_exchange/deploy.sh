#!/bin/bash
echo "🚀 Desplegando Global Exchange en producción..."
set -e

# ============================
# 🏷  OBTENER ÚLTIMO TAG DE GIT
# ============================
# echo "🔍 Buscando último tag de Git..."
# git fetch --tags --force >/dev/null 2>&1 || true

# ULTIMO_TAG=$(git describe --tags "$(git rev-list --tags --max-count=1)")

# if [ -z "$ULTIMO_TAG" ]; then
#     echo "⚠️  No se encontró ningún tag. Usando 'latest' por defecto."
#     ULTIMO_TAG="latest"
# fi

# echo "🏷  Versión a desplegar: $ULTIMO_TAG"

# # Exportar para que docker-compose lo pueda usar (${APP_VERSION})
# export APP_VERSION="$ULTIMO_TAG"

# # Si querés desplegar exactamente el código de ese tag (opcional):
# git checkout "$ULTIMO_TAG"


FILE="docker-compose.prod.yml"

# ============================
# 🧹 Detener y limpiar previos
# ============================
echo "🧹 Deteniendo y limpiando contenedores anteriores..."
docker compose -f "$FILE" down -v --remove-orphans

# ============================
# 🔨 Build + Up
# ============================
echo "🔨 Construyendo servicios..."
docker compose -f "$FILE" build --pull

echo "🚀 Levantando servicios en segundo plano..."
docker compose -f "$FILE" up -d

# ============================
# ⏳ Esperar inicio
# ============================
echo "⏳ Esperando a que los servicios estén listos..."
sleep 10

echo "📊 Estado de contenedores inicial:"
docker compose -f "$FILE" ps

# ============================
# 🔍 Esperar health de PostgreSQL
# ============================
echo "🔍 Verificando salud de PostgreSQL..."

MAX_ATTEMPTS=30
ATTEMPT=0

until [ "$(docker compose -f "$FILE" ps --format json db | grep -o '"Health":"[^"]*"' | cut -d'"' -f4)" = "healthy" ] || [ $ATTEMPT -ge $MAX_ATTEMPTS ]; do
    ATTEMPT=$((ATTEMPT+1))
    echo "⏳ PostgreSQL no está listo... ($ATTEMPT/$MAX_ATTEMPTS)"
    sleep 2
done

if [ $ATTEMPT -ge $MAX_ATTEMPTS ]; then
    echo "❌ PostgreSQL no está saludable después de $MAX_ATTEMPTS intentos"
    docker compose -f "$FILE" logs db
    exit 1
fi

echo "✅ PostgreSQL está healthy"

# ============================
# 🔧 Configuración PostgreSQL remota
# ============================
echo "🔧 Configurando PostgreSQL para conexiones remotas..."

if [ -f configure-postgres.sh ]; then
    chmod +x configure-postgres.sh
    ./configure-postgres.sh || true
else
    echo "⚠️ No se encontró configure-postgres.sh. Configurando manualmente..."
    docker compose -f "$FILE" exec -T db bash -c "cat > /var/lib/postgresql/data/pg_hba.conf << 'EOF'
# TYPE  DATABASE        USER            ADDRESS                 METHOD
local   all             all                                     trust
host    all             all             127.0.0.1/32            trust
host    all             all             ::1/128                 trust
host    all             all             0.0.0.0/0               md5
host    all             all             192.168.0.0/16          md5
host    all             all             172.0.0.0/8             md5
EOF"
    docker compose -f "$FILE" exec -T db bash -c "psql -U postgres -c 'SELECT 1'" # Reload seguro
fi

sleep 3

# ============================
# 🔄 Migraciones + Static
# ============================
echo "🔄 Ejecutando migraciones..."
docker compose -f "$FILE" exec -T web python manage.py migrate --noinput

echo "📦 Copiando archivos estáticos..."
docker compose -f "$FILE" exec -T web python manage.py collectstatic --noinput

# ============================
# ✅ Verificar static en Nginx
# ============================
echo "🔍 Verificando archivos estáticos en Nginx..."
docker compose -f "$FILE" exec -T nginx ls -la /app/staticfiles

# ============================
# 📥 Cargar datos iniciales
# ============================
echo "📥 Cargando datos iniciales..."
docker compose -f "$FILE" exec -T web python manage.py shell < global_exchange/core/scripts/default_data.py

echo "🏦 Ejecutando poblar datos iniciales..."
docker compose -f "$FILE" exec -T web python poblar_datos_iniciales.py

echo "🏦 Ejecutando poblar.py (TAUSER)..."
docker compose -f "$FILE" exec -T web python poblar.py

# ============================
# 🏁 Final
# ============================
echo ""
echo "✅ Despliegue completado exitosamente!"
echo ""
echo "📌 URLs de acceso:"
echo "   - Web: http://192.168.100.168"
echo ""
echo "🗄 PostgreSQL:"
echo "   - Host: 192.168.100.168"
echo "   - Puerto: 5432"
echo "   - Base: db_global_exchange"
echo "   - Usuario: postgres"
echo "   - Contraseña: 1234"
echo ""
echo "💡 Conexión DBeaver:"
echo "   jdbc:postgresql://192.168.100.168:5432/db_global_exchange"
