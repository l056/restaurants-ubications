# Usamos una imagen oficial de Python 3.10
FROM python:3.10-slim

# Actualizamos e instalamos dependencias
RUN apt-get update && apt-get install -y \
    curl \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# Establecemos el directorio de trabajo
WORKDIR /app

# Copiamos los archivos de requisitos
COPY requirements.txt .

# Instalamos las dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Copiamos el resto del código de la aplicación
COPY . .

# Exponemos el puerto en el que correrá la aplicación
EXPOSE 5000

# Comando para correr el script de inicialización y luego la aplicación
CMD ["sh", "-c", "python init_db.py && flask --app src.factory.factory:create_app run --host=0.0.0.0"]
