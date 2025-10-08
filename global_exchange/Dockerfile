FROM python:3.12-slim

WORKDIR /app

# Instalar dependencias del sistema (incluir postgresql-client para wait-for-it.sh)
RUN apt-get update && \
    apt-get install -y gcc libpq-dev postgresql-client && \
    rm -rf /var/lib/apt/lists/*

# Instalar dependencias Python
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copiar código de la aplicación
COPY . .

# Copiar y dar permisos al script de espera
COPY wait-for-it.sh /wait-for-it.sh
RUN chmod +x /wait-for-it.sh

EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "global_exchange.wsgi:application"]