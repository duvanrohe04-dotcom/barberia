# 🚀 GUÍA PARA DESPLEGAR CAMBIOS DE WHATSAPP

## ✅ Cambios Realizados

1. **Mejorado el formato de números de WhatsApp** - Ahora agrega `@s.whatsapp.net` automáticamente
2. **Agregados logs detallados** - Para ver exactamente qué está pasando
3. **Mejor manejo de errores** - Mensajes más claros cuando algo falla
4. **Mensaje más completo** - Incluye teléfono del cliente y nombre de la tienda

## 📋 Pasos para Desplegar

### Opción 1: Si usas Git (Recomendado)

```bash
# 1. Asegúrate de estar en la carpeta del proyecto
cd /ruta/a/tu/proyecto

# 2. Guarda los cambios en Git
git add .
git commit -m "Mejorar notificaciones de WhatsApp"

# 3. Sube los cambios a tu repositorio
git push origin main

# 4. En tu servidor, actualiza el código
# (Esto depende de tu plataforma de hosting)
```

### Opción 2: Si usas Docker Compose directamente

```bash
# 1. Sube los archivos modificados a tu servidor
# Archivos modificados:
# - app/whatsapp_service.py
# - app/routes/api.py
# - requirements.txt

# 2. Conéctate a tu servidor por SSH
ssh usuario@tu-servidor.com

# 3. Ve a la carpeta del proyecto
cd /ruta/a/tu/proyecto

# 4. Detén los contenedores
docker-compose down

# 5. Reconstruye la imagen con los cambios
docker-compose build web

# 6. Inicia los contenedores
docker-compose up -d

# 7. Verifica que todo esté corriendo
docker-compose ps
```

### Opción 3: Si usas Railway/Render/Heroku

Estos servicios se actualizan automáticamente cuando haces `git push`:

```bash
# 1. Guarda los cambios
git add .
git commit -m "Mejorar notificaciones de WhatsApp"

# 2. Sube a tu repositorio
git push origin main

# Railway/Render detectará los cambios y desplegará automáticamente
```

## 🔍 Verificar que Funcione

### 1. Verificar que Evolution API esté corriendo

```bash
# Ver todos los contenedores
docker-compose ps

# Deberías ver algo como:
# evolution_api    Up 5 minutes    0.0.0.0:8085->8080/tcp
```

### 2. Verificar que WhatsApp esté conectado

1. Ve al panel de administrador
2. Sección "Configuración"
3. Click en "🔗 Vincular WhatsApp (QR)"
4. Debería decir: **"✅ WhatsApp ya está vinculado y activo"**

Si no está conectado:
- Escanea el código QR con tu WhatsApp
- Espera a que se conecte (puede tardar unos segundos)

### 3. Probar con una cita de prueba

1. Crea una cita de prueba desde la página
2. Revisa los logs del servidor:

```bash
# Ver logs en tiempo real
docker-compose logs -f web

# O solo las últimas 100 líneas
docker-compose logs --tail 100 web
```

Deberías ver algo como:
```
[WhatsApp] Iniciando notificación de nueva cita
[WhatsApp] Cliente: Juan Pérez
[WhatsApp] Empleado: Alejandro Ruiz
[WhatsApp] Enviando a empleado: Alejandro Ruiz - 3001234567
[WhatsApp] Enviando mensaje a: 573001234567@s.whatsapp.net
[WhatsApp] Instancia: jsbarbershop
[WhatsApp] URL: http://evolution_api:8080/message/sendText/jsbarbershop
[WhatsApp] Status: 200
[WhatsApp] Respuesta: {"key":{"remoteJid":"573001234567@s.whatsapp.net"...}}
[WhatsApp] ✅ Mensaje enviado exitosamente
```

### 4. Verificar que el empleado recibió el mensaje

El empleado debería recibir un mensaje como:
```
🚨 NUEVA RESERVACIÓN 💈

👤 Cliente: Juan Pérez
📞 Teléfono: 3001234567
✂️ Servicio: Corte de Cabello
📅 Fecha: 2026-05-01
🕐 Hora: 15:30
💰 Total: $25000

Te han agendado una cita en JS BARBERSHOP.
```

## ❌ Solución de Problemas

### Problema: "WhatsApp no está conectado"

**Solución:**
1. Ve a Configuración → Vincular WhatsApp
2. Escanea el QR con tu WhatsApp
3. Espera a que se conecte

### Problema: "Error de conexión con Evolution API"

**Solución:**
```bash
# Verificar que Evolution API esté corriendo
docker-compose ps evolution_api

# Si no está corriendo, iniciarlo
docker-compose up -d evolution_api

# Ver logs de Evolution API
docker-compose logs evolution_api
```

### Problema: "El empleado no recibe el mensaje"

**Verificar:**
1. ¿El empleado tiene teléfono configurado en el panel de admin?
2. ¿El número está en formato correcto? (10 dígitos sin espacios)
3. ¿WhatsApp está conectado?
4. ¿Los logs muestran "✅ Mensaje enviado exitosamente"?

### Problema: "Logs muestran error 401 o 403"

**Solución:**
La API key es incorrecta. Verifica que en `docker-compose.yml`:
- `EVOLUTION_API_KEY` en el servicio `web` coincida con
- `AUTHENTICATION_API_KEY` en el servicio `evolution_api`

## 📝 Notas Importantes

1. **Los cambios solo funcionarán después de desplegar** - El código local no puede conectarse a Evolution API
2. **Necesitas reinstalar dependencias** - Se agregó `qrcode` y `pillow` a requirements.txt
3. **Los logs son tu mejor amigo** - Siempre revisa los logs para ver qué está pasando
4. **Prueba con tu propio número primero** - Antes de probar con clientes reales

## ✅ Checklist Final

- [ ] Código subido al servidor
- [ ] Contenedores reconstruidos y reiniciados
- [ ] Evolution API corriendo (`docker-compose ps`)
- [ ] WhatsApp conectado (escanear QR si es necesario)
- [ ] Empleados tienen teléfonos configurados
- [ ] Cita de prueba creada
- [ ] Logs revisados
- [ ] Mensaje recibido por el empleado

---

**¿Necesitas ayuda?** Revisa los logs con `docker-compose logs -f web` y busca mensajes que empiecen con `[WhatsApp]`.
