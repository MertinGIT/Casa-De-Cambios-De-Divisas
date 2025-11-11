#!/bin/bash

echo "🛠 Desplegando entorno de desarrollo..."

# 1. Detener contenedores viejos
docker-compose down

# 2. Reconstruir imágenes
docker-compose build

# 3. Levantar contenedores en background
docker-compose up -d

echo "⏳ Esperando que la base de datos inicie..."
sleep 5

echo "🔄 Ejecutando migraciones..."
docker-compose exec web python manage.py migrate

echo "📥 Cargando datos iniciales..."
docker-compose exec web python manage.py loaddata initial_data.json || true
docker-compose exec web python manage.py shell < global_exchange/core/scripts/default_data.py

echo "🏦 Ejecutando poblar.py (TAUSER)..."
docker-compose exec web python poblar.py

echo "✅ Despliegue DEV listo en http://localhost:8000"

echo "📥 Cargando datos iniciales (idempotente)…"
docker-compose exec web python poblar_datos_iniciales.py
