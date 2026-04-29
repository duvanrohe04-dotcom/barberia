# BarberKing - Sistema de Gestión de Barbería

## 🚀 Configuración en Coolify

### Paso 1: Acceder a Coolify
1. Abre tu instancia de Coolify
2. Ve a tu proyecto "BarberKing"
3. Haz clic en **Settings** o **Configuration**

### Paso 2: Configurar Variables de Entorno
En la sección **"Environment Variables"**, agrega estas variables:

```
FLASK_ENV=production
SECRET_KEY=cambia-esto-por-una-clave-segura-de-64-caracteres
POSTGRES_USER=barberking
POSTGRES_PASSWORD=tu_password_seguro
POSTGRES_DB=barberking_db
DATABASE_URL=postgresql://barberking:tu_password_seguro@db:5432/barberking_db
```

**⚠️ Importante:** Reemplaza `tu_password_seguro` con una contraseña segura (mínimo 12 caracteres). Usa la misma contraseña en `POSTGRES_PASSWORD` y en `DATABASE_URL`.

### Paso 3: Hacer Deploy
1. Guarda los cambios
2. Haz clic en **"Deploy"** o **"Redeploy"**
3. Espera a que se construyan los contenedores (5-10 minutos)
4. Verifica los logs

### Paso 4: Verificar que Funciona
- Abre tu navegador en tu dominio o IP de Coolify
- Deberías ver la aplicación funcionando

## 🆘 Solución de Problemas

### Error: "Database is uninitialized"
- Verifica que `POSTGRES_PASSWORD` está configurado
- Verifica que `DATABASE_URL` tiene la contraseña correcta
- Haz un redeploy

### Error: "Connection refused"
- Espera a que PostgreSQL se inicie (1-2 minutos)
- Verifica que `DATABASE_URL` apunta a `db` (no a `localhost`)
- Haz un redeploy

### Error: "ModuleNotFoundError: No module named 'psycopg2'"
- Verifica que `requirements.txt` tiene `psycopg2-binary`
- Haz un redeploy

## 📋 Checklist Antes de Deploy
- ✅ `FLASK_ENV=production`
- ✅ `SECRET_KEY` está configurado
- ✅ `POSTGRES_USER=barberking`
- ✅ `POSTGRES_PASSWORD` está configurado (contraseña segura)
- ✅ `POSTGRES_DB=barberking_db`
- ✅ `DATABASE_URL` tiene la contraseña correcta
- ✅ Hiciste clic en "Deploy" o "Redeploy"

## 🎉 ¡Listo!
Una vez configurado, tu aplicación debería estar funcionando correctamente en Coolify.
