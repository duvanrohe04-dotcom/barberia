#!/bin/bash
set -e

chmod -R 777 /app/instance /app/app/static/uploads 2>/dev/null || true

exec "$@"
