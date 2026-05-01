FROM python:3.11-slim

# Configurar zona horaria de Colombia (UTC-5)
ENV TZ=America/Bogota
RUN apt-get update && apt-get install -y --no-install-recommends \
    tzdata && \
    ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && \
    echo $TZ > /etc/timezone

WORKDIR /app

# Dependencias del sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc curl && \
    rm -rf /var/lib/apt/lists/*

# Instalar dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código (sin la DB local ni uploads)
COPY . .

# Eliminar cualquier DB local que haya sido copiada accidentalmente
# Los datos reales vienen del volumen Docker, no del código
RUN rm -f /app/instance/*.db /app/instance/*.sqlite3

# Crear directorios necesarios
RUN mkdir -p /app/instance /app/app/static/uploads

# Copiar entrypoint y dar permisos
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 81

# Healthcheck interno de Docker para monitorizar estado
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:81/api/health || exit 1

ENTRYPOINT ["/entrypoint.sh"]
CMD ["gunicorn", "--bind", "0.0.0.0:81", "--workers", "2", "--threads", "2", "--timeout", "60", "--preload", "run:app"]
