# Usamos imagen oficial de Python 3.12.1
FROM python:3.12.1

# Definimos carpeta de trabajo dentro del contenedor
WORKDIR /app

# Instalamos dependencias del sistema necesarias para psycopg2 (PostgreSQL)
RUN apt-get update && apt-get install -y gcc libpq-dev && rm -rf /var/lib/apt/lists/*

# Copiamos el archivo requirements.txt para instalar dependencias Python
COPY requirements.txt .

# Instalamos las dependencias Python
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copiamos el resto del código al contenedor
COPY . .

# Exponemos el puerto 8000 para el servidor Django
EXPOSE 8000

# Comando para correr el servidor Django
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
