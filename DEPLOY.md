# 🚀 Guía de Despliegue en Coolify

## Requisitos Previos
- Cuenta en Coolify
- Repositorio Git conectado

## Pasos para Desplegar

### 1. Configurar Variables de Entorno en Coolify

En el panel de Coolify, configura estas variables de entorno:

```bash
FLASK_ENV=production
SECRET_KEY=tu-clave-secreta-muy-segura-de-64-caracteres-minimo
DATABASE_URL=sqlite:///barberking.db
GUNICORN_WORKER_ID=0
```

**Importante:** Cambia `SECRET_KEY` por una clave aleatoria segura.

### 2. Configurar Puerto

- Puerto de la aplicación: **81**
- Coolify automáticamente expondrá esto en el puerto 80/443

### 3. Configurar Volúmenes (Persistencia de Datos)

En Coolify, agrega estos volúmenes persistentes:

```
/app/instance -> Persistir base de datos
/app/app/static/uploads -> Persistir imágenes subidas
```

### 4. Desplegar

1. Conecta tu repositorio Git en Coolify
2. Selecciona la rama principal (main/master)
3. Coolify detectará automáticamente el `Dockerfile`
4. Haz clic en "Deploy"

### 5. Verificar Despliegue

Una vez desplegado, verifica:

- ✅ La página carga correctamente
- ✅ Puedes hacer login con: `admin` / `barberking2024`
- ✅ Las imágenes se cargan correctamente
- ✅ Las reservas funcionan

## Solución de Problemas

### Error: "Application failed to start"

**Solución:**
1. Verifica que las variables de entorno estén configuradas
2. Revisa los logs en Coolify
3. Asegúrate de que el puerto 81 esté configurado

### Error: "Database locked"

**Solución:**
1. Verifica que el volumen `/app/instance` esté configurado
2. Reinicia el contenedor

### Error: "Permission denied"

**Solución:**
1. Verifica que los volúmenes tengan permisos correctos
2. El contenedor usa el usuario `appuser` (no root)

## Actualizar la Aplicación

Para actualizar después de hacer cambios:

1. Haz commit y push de tus cambios
2. En Coolify, haz clic en "Redeploy"
3. Coolify reconstruirá y desplegará automáticamente

## Credenciales por Defecto

- **Usuario:** admin
- **Contraseña:** barberking2024

**⚠️ IMPORTANTE:** Cambia estas credenciales inmediatamente después del primer login desde el panel de administración.

## Backup de Datos

Los datos importantes están en:
- `/app/instance/barberking.db` - Base de datos
- `/app/app/static/uploads/` - Imágenes subidas

Coolify mantiene estos datos en volúmenes persistentes.

## Soporte

Si tienes problemas, revisa:
1. Logs de Coolify
2. Variables de entorno configuradas
3. Volúmenes montados correctamente
