FROM python:3.11-slim

WORKDIR /app

# Dependencias del sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc && \
    rm -rf /var/lib/apt/lists/*

# Instalar dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY . .

# Eliminar cualquier DB local que haya sido copiada accidentalmente
RUN rm -f /app/instance/*.db /app/instance/*.sqlite3

# Crear carpetas necesarias
RUN mkdir -p /app/instance /app/app/static/uploads

# Hacer ejecutable el script de entrada
RUN chmod +x /app/entrypoint.sh

# Usuario no-root por seguridad
RUN useradd -m appuser && chown -R appuser /app
USER appuser

EXPOSE 81

# Usar el script de entrada
ENTRYPOINT ["/app/entrypoint.sh"]
