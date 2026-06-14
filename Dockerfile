# syntax=docker/dockerfile:1
FROM python:3.11-slim

# Configurar zona horaria de Colombia (UTC-5)
ARG DEBIAN_FRONTEND=noninteractive
ENV TZ=America/Bogota
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    tzdata && \
    ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && \
    echo $TZ > /etc/timezone

WORKDIR /app

# Dependencias del sistema (solo lo mínimo para entrypoint.sh)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 curl postgresql-client-17 && \
    rm -rf /var/lib/apt/lists/*

# Instalar dependencias Python (usando ruedas binarias prioritariamente)
COPY requirements.txt .
RUN pip install --no-cache-dir --prefer-binary -r requirements.txt

# Copiar código (sin la DB local ni uploads)
COPY . .

# Eliminar cualquier DB local que haya sido copiada accidentalmente
RUN rm -f /app/instance/*.db /app/instance/*.sqlite3

# Crear carpetas para volúmenes
RUN mkdir -p /app/instance /app/app/static/uploads

# Backup de archivos estáticos para sobrescribir el volumen montado en runtime
RUN mkdir -p /app-static && cp -r /app/app/static/js /app/app/static/css /app-static/

# Entrypoint para inicialización (crea rol admin en BD)
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Usuario no-root por seguridad
RUN useradd -m appuser && chown -R appuser /app && chown -R appuser /app-static
USER appuser

EXPOSE 80

# Healthcheck interno
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:80/api/health || exit 1

ENTRYPOINT ["/entrypoint.sh"]
CMD ["gunicorn", "--bind", "0.0.0.0:80", "--workers", "2", "--threads", "2", "--timeout", "60", "run:app"]
