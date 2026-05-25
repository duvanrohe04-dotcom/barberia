# 🔐 CONFIGURACIÓN DE VARIABLES DE ENTORNO

## ✅ Cambios Realizados

Todas las variables hardcadiadas se han extraído a archivos `.env`:

```
❌ ANTES: SECRET_KEY=barberking_super_secret_key_fixed (en docker-compose.yml)
✅ AHORA: SECRET_KEY=${SECRET_KEY} (lee desde .env)
```

## 📂 Archivos de Configuración

| Archivo | Propósito | Usar en |
|---------|-----------|---------|
| `.env` | Variables de producción (PRIVADO) | Coolify / Servidor |
| `.env.example` | Plantilla con instrucciones | Referencia |
| `.env.local` | Variables para desarrollo local | Local (Windows) |

## 🚀 SETUP INICIAL

### 1️⃣ OPCIÓN A: Desarrollo Local (Windows)

```bash
# El archivo .env.local ya está creado
# Solo abre y verifica que contenga:

FLASK_ENV=development
SECRET_KEY=dev_secret_key_cambiar_en_produccion
```

Cuando ejecutes `python run.py`, la app usará **SQLite** automáticamente.

---

### 2️⃣ OPCIÓN B: En Coolify (Producción)

Completa el archivo `.env` con valores REALES:

```bash
# Edita .env y cambia estos valores:

FLASK_ENV=production
FLASK_APP=run.py
SECRET_KEY=tu_clave_secreta_fuerte_aqui_minimo_32_caracteres

POSTGRES_USER=barber_user
POSTGRES_PASSWORD=tu_contrasena_fuerte_aqui
POSTGRES_DB=barberking_db
POSTGRES_HOST=postgres-db
POSTGRES_PORT=5432

EVOLUTION_API_KEY=tu_clave_api_evolution
EVOLUTION_SERVER_URL=https://tu-dominio.com
```

---

## 🔑 Generar Claves Seguras

### SECRET_KEY (para Flask)

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Salida ejemplo: `a3f2b1c8d9e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9`

### POSTGRES_PASSWORD (para Base de Datos)

```bash
python -c "import secrets; print(secrets.token_urlsafe(16))"
```

Salida ejemplo: `kJ8_mNp2Q3rT4sUvW-xYz`

### EVOLUTION_API_KEY (para WhatsApp)

```bash
python -c "import secrets; print(secrets.token_hex(16))"
```

Salida ejemplo: `c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9`

---

## 📋 Variables Disponibles en .env

### Flask & App
```env
FLASK_ENV=production              # production o development
FLASK_APP=run.py                  # Archivo de entrada
SECRET_KEY=...                    # Clave de sesión (64+ caracteres)
MAX_CONTENT_LENGTH=5242880        # Límite de uploads (5MB)
```

### PostgreSQL Database
```env
POSTGRES_USER=barber_user         # Usuario de BD
POSTGRES_PASSWORD=...             # Contraseña BD
POSTGRES_DB=barberking_db         # Nombre de BD
POSTGRES_HOST=postgres-db         # Host (docker) o localhost
POSTGRES_PORT=5432                # Puerto
DATABASE_URL=...                  # URL de conexión (automática)
```

### Evolution API (WhatsApp)
```env
EVOLUTION_API_URL=http://evolution_api:8080  # URL del API
EVOLUTION_API_KEY=...                        # Clave API
EVOLUTION_DB_HOST=postgres-db                # Host BD
EVOLUTION_DB_USER=barber_user                # Usuario BD
EVOLUTION_DB_PASSWORD=...                    # Contraseña BD
EVOLUTION_DB_NAME=evolution_db               # Nombre BD
EVOLUTION_SERVER_URL=https://tu-dominio.com # URL pública
```

### Redis (Cache)
```env
REDIS_HOST=redis                  # Host (docker) o localhost
REDIS_PORT=6379                   # Puerto
REDIS_PREFIX=barber               # Prefijo de claves
```

### Config General
```env
TZ=America/Bogota                 # Zona horaria
RATELIMIT_STORAGE_URI=memory://   # Storage para rate limiting
```

---

## 📝 Configuración en Coolify

1. Ve a tu proyecto en Coolify
2. **Settings** → **Variables**
3. Crea cada variable manualmente O importa desde archivo

### Importar desde archivo (.env):

```bash
# En tu máquina local
cat .env  # Copia el contenido

# En Coolify:
# 1. Settings → Variables
# 2. Pega cada línea: KEY=VALUE
```

### ⚠️ Variables Críticas en Coolify:

Asegúrate que TODAS estas existan:
- [ ] `FLASK_ENV=production`
- [ ] `SECRET_KEY=` (clave fuerte)
- [ ] `POSTGRES_PASSWORD=` (contraseña fuerte)
- [ ] `EVOLUTION_API_KEY=` (clave API)
- [ ] `EVOLUTION_SERVER_URL=` (tu dominio)

---

## 🔒 Seguridad

### ✅ HECHO: Extractas variables de código

```
✅ docker-compose.yml - Ahora usa ${VARIABLE_NAME}
✅ app/__init__.py - Ahora valida SECRET_KEY
✅ migration scripts - Leen de .env
```

### ✅ HECHO: Crear .env distinto para local vs prod

```
✅ .env.local - Desarrollo (SQLite)
✅ .env - Producción (PostgreSQL)
✅ .env.example - Plantilla sin secretos
```

### ⚠️ NUNCA hagas commit de .env

```bash
# Asegúrate que .gitignore contiene:
echo ".env" >> .gitignore
echo ".env.local" >> .gitignore

# Verifica:
git status
# No debe mostrar archivos .env
```

---

## 🧪 Verificar Configuración

### Local (Windows)

```bash
# Verifica que se usan variables
python run.py

# Deberías ver algo como:
# WARNING in app.logger: SECRET_KEY is set to default value
# (solo en desarrollo, no en producción)
```

### Producción (Coolify)

```bash
# En Coolify → Deployments → Logs
# Deberías VER:
✅ DATABASE_URL=postgresql://...
✅ EVOLUTION_API_KEY=...
✅ SECRET_KEY=...

# Deberías NO VER:
❌ Valores hardcadiados
❌ Claves por defecto
```

---

## 🆘 Solucionar Problemas

### Error: "SECRET_KEY not defined"

```
Solución: 
1. Abre .env
2. Encuentra SECRET_KEY=
3. Remplaza el valor con una clave segura
4. Guarda el archivo
```

### Error: "Cannot connect to database"

```
Solución:
1. Verifica POSTGRES_PASSWORD en .env
2. Verifica POSTGRES_HOST es correcto (postgres-db en Docker)
3. Verifica DATABASE_URL está completa
```

### Valores hardcadiados aún presentes

```bash
# Busca hardcadiadas:
grep -r "barberking_secret_key" .
grep -r "barber_pass" .

# No deberían encontrarse en código, solo en .env.example
```

---

## ✨ Beneficios

✅ No hay secretos en código  
✅ Fácil cambiar configuración  
✅ Diferente config local vs producción  
✅ Cumple con seguridad  
✅ Compatible con Coolify  

---

**Próximo paso:** Llena `.env` con valores reales y haz deploy en Coolify 🚀
