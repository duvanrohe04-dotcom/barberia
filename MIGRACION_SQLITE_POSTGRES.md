# 🗄️ MIGRACIÓN: SQLite → PostgreSQL

## 📋 Resumen
Cambiarás tu base de datos de **SQLite** (actual en Coolify) a **PostgreSQL** sin perder datos.

### Configuración final:
- **Local (Windows)**: SQLite (`instance/barberking.db`) ✅
- **Coolify (Servidor)**: PostgreSQL (`barberking_db`) ✅

---

## ⚙️ PASO 1: Configurar PostgreSQL Local

### Si tienes PostgreSQL instalado localmente:

```bash
# 1. Verificar que PostgreSQL está corriendo
psql --version

# 2. Asegúrate que el usuario existe
# Abre pgAdmin o ejecuta:
# CREATE USER barber_user WITH PASSWORD 'barber_pass';
# CREATE DATABASE barberking_db OWNER barber_user;
```

### Si usas Docker:

```bash
# En la carpeta del proyecto
docker-compose up -d postgres redis

# Esperar a que PostgreSQL esté listo (5-10 segundos)
docker-compose logs postgres
# Deberías ver: "PostgreSQL init process complete. Ready for start up."
```

---

## ⚙️ PASO 2: Inicializar Base de Datos PostgreSQL

```bash
# Crear la base de datos barberking_db
python setup_postgres.py

# Salida esperada:
# ✅ Base de datos 'barberking_db' ya existe
# ✅ POSTGRESQL LISTO
```

---

## 📦 PASO 3: Migrar Datos (sin perder nada)

```bash
# Exportar datos de SQLite → PostgreSQL
python migrate_data_safely.py

# Salida esperada:
# 🚀 INICIO DE MIGRACIÓN DE DATOS
# ✅ Backup creado: backup_sqlite_20260525_120000.db
# 📚 Tablas a migrar:
#   - shop_config
#   - services
#   - staff
#   - admins
#   - appointments
#   - reviews
# ⚙️  Migrando datos...
# ✅ MIGRACIÓN COMPLETADA
#    Total de registros migrados: 150
#    Backup guardado en: backup_sqlite_20260525_120000.db
```

⚠️ **Importante**: Se crea un **BACKUP AUTOMÁTICO** de tu SQLite antes de migrar.

---

## ✅ PASO 4: Verificar que todo funciona en Local

```bash
# Activar entorno virtual (ya deberías estar dentro)
# Si no:
# .\venv\Scripts\Activate.ps1

# Correr la app localmente
python run.py

# Acceder a: http://localhost:81
# Verifica que veas tus datos (servicios, staff, citas, etc.)
```

✅ Deberías ver tus datos migrados desde SQLite

---

## 🚀 PASO 5: Preparar para Coolify

### En Coolify - Actualizar Variables de Entorno:

Cambia **SOLO** esta variable:

| Variable | Valor Actual (SQLite) | Nuevo Valor (PostgreSQL) |
|----------|----------------------|--------------------------|
| `DATABASE_URL` | `sqlite:////app/instance/barberking.db` | `postgresql://barber_user:barber_pass@postgres:5432/barberking_db` |

**Las otras variables quedan igual:**
- `FLASK_ENV=production` 
- `SECRET_KEY=barberking_super_secret_key_fixed`
- `EVOLUTION_API_URL=http://evolution_api:8080`
- `EVOLUTION_API_KEY=barberking_secret_key`

### Acciones en Coolify:

1. Ve a **Settings** → **Environment**
2. Busca `DATABASE_URL`
3. Cambia el valor a: `postgresql://barber_user:barber_pass@postgres:5432/barberking_db`
4. Guarda cambios
5. Redeploy: Ve a **Deployments** → **Redeploy**

---

## 🔍 VERIFICACIÓN FINAL

### En Coolify (después del redeploy):

```bash
# Conectar a PostgreSQL desde Coolify
# Ir a: https://tu-dominio.com

# Verificar que funciona:
# ✅ Puedes login con tu admin
# ✅ Ves todos los servicios
# ✅ Ves todo el staff
# ✅ Ves las citas históricas
# ✅ Las nuevas citas se guardan
```

---

## 📊 Ventajas de PostgreSQL en Coolify

✅ **Mejor rendimiento** con múltiples usuarios  
✅ **Datos persistentes** en volúmenes Docker  
✅ **Backups automáticos** con Coolify  
✅ **Soporte para transacciones** más complejas  
✅ **Escalabilidad** para futuros crecimientos  

---

## 🆘 Solucionar Problemas

### Error: "No se puede conectar a PostgreSQL"

```bash
# Verificar que PostgreSQL está corriendo
docker-compose ps postgres

# Si no está corriendo:
docker-compose up -d postgres

# Ver logs
docker-compose logs postgres
```

### Error: "Base de datos barberking_db no existe"

```bash
python setup_postgres.py
```

### Error: "No se pueden migrar los datos"

```bash
# Verificar que SQLite tiene datos
sqlite3 instance/barberking.db "SELECT COUNT(*) FROM admins;"

# Revisar los logs del script de migración
python migrate_data_safely.py
```

### Restaurar desde Backup

```bash
# Si algo salió mal, restaura el backup:
cp backup_sqlite_20260525_120000.db instance/barberking.db

# Y vuelve a correr la migración
python migrate_data_safely.py
```

---

## 📝 Checklista de Migración

- [ ] PostgreSQL está instalado/corriendo
- [ ] `setup_postgres.py` ejecutado exitosamente
- [ ] `migrate_data_safely.py` ejecutado sin errores
- [ ] Backup SQLite creado: `backup_sqlite_*.db`
- [ ] App funciona en local y veo los datos
- [ ] `docker-compose.yml` actualizado ✅ (ya está hecho)
- [ ] `DATABASE_URL` actualizado en Coolify
- [ ] Redeploy en Coolify completado
- [ ] Verificar que app funciona en producción

---

## 🎉 ¡Listo!

Tu aplicación ahora está usando **PostgreSQL en Coolify** y **SQLite en local**, con todos tus datos migrados sin pérdida.

### Próximos pasos (opcional):

1. **Eliminar SQLite en Coolify** (ya no se necesita) ✅ (ya hecho en docker-compose.yml)
2. **Configurar backups automáticos** de PostgreSQL en Coolify
3. **Monitorear** el rendimiento de la app

---

¿Preguntas? Revisa los logs:
- Local: `python run.py` (verás los errores en consola)
- Coolify: Ve a **Deployments** → **Logs**
