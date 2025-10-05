#!/bin/bash

echo "🚀 Desplegando Global Exchange en producción..."

# Levantar contenedores sin eliminar volúmenes
docker compose -f docker-compose.prod.yml up -d --build

# Ejecutar migraciones (para actualizar la DB)
docker compose -f docker-compose.prod.yml exec web python manage.py migrate

# Copiar archivos estáticos
docker compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput

# Recargar nginx por si hay cambios en static
docker compose -f docker-compose.prod.yml exec nginx nginx -s reload

echo "✅ Producción lista en http://192.168.100.159"
