#!/bin/sh
# wait-for-it.sh

set -e

host="$1"
shift

echo "Esperando a que $host esté disponible..."

# Usar las variables de entorno directamente
until PGPASSWORD="$DJANGO_DB_PASSWORD" psql -h "$host" -U "$DJANGO_DB_USER" -d "$DJANGO_DB_NAME" -c '\q' 2>/dev/null; do
  echo "PostgreSQL no disponible - esperando..."
  sleep 2
done

echo "PostgreSQL está disponible - iniciando aplicación"
exec "$@"