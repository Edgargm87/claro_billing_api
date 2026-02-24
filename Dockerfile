# Imagen base ligera de Python
FROM python:3.11-slim

# Evitar que Python genere .pyc y buffer de stdout
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Directorio de trabajo dentro del contenedor
WORKDIR /app

# Instalar dependencias del sistema (si luego necesitas psycopg2, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements primero para aprovechar cache de Docker
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código de la aplicación
COPY app ./app

# Exponer el puerto donde corre Uvicorn
EXPOSE 8000

# Comando por defecto: levantar Uvicorn con la app principal
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
