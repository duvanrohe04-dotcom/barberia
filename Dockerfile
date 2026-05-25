# syntax=docker/dockerfile:1
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
RUN rm -f /app/instance/*.db /app/instance/*.sqlite3

# Crear carpetas para volúmenes
RUN mkdir -p /app/instance /app/app/static/uploads

# Usuario no-root por seguridad
RUN useradd -m appuser && chown -R appuser /app
USER appuser

EXPOSE 80

# Healthcheck interno
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:80/api/health || exit 1

CMD ["gunicorn", "--bind", "0.0.0.0:80", "--workers", "2", "--threads", "2", "--timeout", "60", "--preload", "run:app"]
