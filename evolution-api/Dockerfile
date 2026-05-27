FROM evoapicloud/evolution-api:v2.3.7

# Permite ejecutar scripts Python que dependan de requests dentro del contenedor.
# Se usa --break-system-packages para Alpine 3.19+ que bloquea pip externo
RUN apk update && apk add --no-cache python3 py3-pip
RUN python3 -m pip install --no-cache-dir --upgrade pip --break-system-packages 2>/dev/null || python3 -m pip install --no-cache-dir --upgrade pip 2>/dev/null || true
RUN python3 -m pip install --no-cache-dir requests --break-system-packages 2>/dev/null || python3 -m pip install --no-cache-dir requests 2>/dev/null || true

CMD ["/bin/sh", "-c", "exec node dist/src/main"]
