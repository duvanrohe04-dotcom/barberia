#!/bin/bash

echo "=========================================="
echo "VERIFICACIÓN DE WHATSAPP"
echo "=========================================="
echo ""

# 1. Verificar que los contenedores estén corriendo
echo "1. Verificando contenedores..."
echo "------------------------------------------"
docker-compose ps | grep -E "(web|evolution_api|redis|postgres)"
echo ""

# 2. Verificar que Evolution API responda
echo "2. Verificando Evolution API..."
echo "------------------------------------------"
curl -s http://localhost:8085 > /dev/null
if [ $? -eq 0 ]; then
    echo "✅ Evolution API está respondiendo"
else
    echo "❌ Evolution API NO está respondiendo"
fi
echo ""

# 3. Ver últimos logs de WhatsApp
echo "3. Últimos logs de WhatsApp..."
echo "------------------------------------------"
docker-compose logs --tail 20 web | grep -i whatsapp
echo ""

# 4. Ver estado de Evolution API
echo "4. Estado de Evolution API..."
echo "------------------------------------------"
docker-compose logs --tail 10 evolution_api
echo ""

echo "=========================================="
echo "VERIFICACIÓN COMPLETADA"
echo "=========================================="
echo ""
echo "Para ver logs en tiempo real:"
echo "  docker-compose logs -f web"
echo ""
echo "Para reiniciar los servicios:"
echo "  docker-compose restart web evolution_api"
