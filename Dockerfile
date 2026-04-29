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

# Usuario no-root por seguridad
RUN useradd -m appuser && chown -R appuser /app
USER appuser

EXPOSE 81

CMD ["gunicorn", "--bind", "0.0.0.0:81", "--workers", "4", "--threads", "2", "--timeout", "60", "run:app"]
