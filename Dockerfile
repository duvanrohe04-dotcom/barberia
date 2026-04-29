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
    libpq-dev gcc && \
    rm -rf /var/lib/apt/lists/*

# Instalar dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código (sin la DB local ni uploads)
COPY . .

# Eliminar cualquier DB local que haya sido copiada accidentalmente
# Los datos reales vienen del volumen Docker, no del código
RUN rm -f /app/instance/*.db /app/instance/*.sqlite3

# Crear carpetas que serán montadas como volúmenes
RUN mkdir -p /app/instance /app/app/static/uploads

# Usuario no-root por seguridad
RUN useradd -m appuser && chown -R appuser /app
USER appuser

EXPOSE 81

CMD ["gunicorn", "--bind", "0.0.0.0:81", "--workers", "2", "--threads", "2", "--timeout", "60", "--preload", "run:app"]
