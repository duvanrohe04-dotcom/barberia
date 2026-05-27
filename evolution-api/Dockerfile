FROM evoapicloud/evolution-api:v2.3.7

# Permite ejecutar scripts Python que dependan de requests dentro del contenedor.
RUN apk add --no-cache python3 py3-pip \
    && python3 -m pip install --no-cache-dir --upgrade pip \
    && python3 -m pip install --no-cache-dir requests

CMD ["/bin/sh", "-c", "exec node dist/src/main"]
