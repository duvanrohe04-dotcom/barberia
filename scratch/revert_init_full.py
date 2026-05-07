import os

file_path = r'c:\Users\ASUS\OneDrive\Desktop\PAGINAS WEB\barberia\app\__init__.py'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Restaurar create_app original
old_init_block = """    with app.app_context():
        global _db_initialized
        with _db_init_lock:
            if not _db_initialized:
                from app import models  # Asegurar que todos los modelos se carguen antes de create_all
                try:
                    db.create_all()
                except Exception as e:
                    print(f"[DB] Advertencia en create_all (posiblemente ya existe o conflicto de hilos): {e}")
                
                try:
                    _migrate_db()
                except Exception as e:
                    print(f"[Migración] Error: {e}")
                
                try:
                    from app.models import seed_data
                    seed_data()
                except Exception as e:
                    print(f"[Seed] Advertencia en seed_data: {e}")
                    
                _db_initialized = True"""

new_init_block = """    with app.app_context():
        global _db_initialized
        with _db_init_lock:
            if not _db_initialized:
                from app import models  # Asegurar que todos los modelos se carguen antes de create_all
                db.create_all()
                try:
                    _migrate_db()
                except Exception as e:
                    print(f"[Migración] Error: {e}")
                from app.models import seed_data, ShopConfig  # noqa: F401
                seed_data()
                _db_initialized = True"""

if old_init_block in content:
    content = content.replace(old_init_block, new_init_block)
else:
    print("Warning: Could not find the exact init block to revert. Skipping create_app restoration.")

# Restaurar _migrate_db original (SQLite)
migrate_start = "def _migrate_db():"
migrate_idx = content.find(migrate_start)

original_migrate = \"\"\"def _migrate_db():
    \"\"\"Agrega columnas nuevas a tablas existentes sin borrar datos.\"\"\"
    from sqlalchemy import text, inspect

    # 1. Primero asegurar que todas las tablas nuevas existan
    db.create_all()

    # 2. Agregar columnas nuevas a tablas existentes
    migrations = [
        "ALTER TABLE staff ADD COLUMN phone VARCHAR(20)",
        "ALTER TABLE services ADD COLUMN duration_minutes INTEGER NOT NULL DEFAULT 60",
        "ALTER TABLE appointments ADD COLUMN duration_minutes INTEGER NOT NULL DEFAULT 60",
        "ALTER TABLE staff ADD COLUMN instagram VARCHAR(100)",
        "ALTER TABLE appointments ADD COLUMN is_free_cut BOOLEAN DEFAULT FALSE",
        "ALTER TABLE appointments ADD COLUMN gender VARCHAR(10) DEFAULT 'male'",
        "ALTER TABLE appointments ADD COLUMN reminder_sent BOOLEAN DEFAULT FALSE",
    ]
    with db.engine.connect() as conn:
        for sql in migrations:
            try:
                conn.execute(text(sql))
                conn.commit()
            except Exception:
                pass  # columna ya existe, ignorar

    # 3. Inicializar ShopConfig con valores por defecto si no existen
    from app.models import ShopConfig
    default_configs = [
        ('shop_name', 'BarberKing'),
        ('shop_logo', ''),
        ('ubicacion', '📍 Bogotá, Colombia'),
        ('telefono', '+57 310 000 0000'),
        ('wa', ''),
        ('ig', ''),
        ('wa_sty', ''),
        ('ig_sty', ''),
        ('evo_instance', 'barberking')
    ]
    for k in ['shop_name', 'shop_logo', 'wa_sty', 'ig_sty', 'evo_instance']:
        if not ShopConfig.query.filter_by(key=k).first():
            db.session.add(ShopConfig(key=k, value='jsbarbershop' if k=='evo_instance' else ''))
    db.session.commit()

    # 4. Verificar y crear tablas críticas...
    inspector = inspect(db.engine)
    existing_tables = inspector.get_table_names()

    with db.engine.connect() as conn:
        # Tabla fidelity_progress
        if 'fidelity_progress' not in existing_tables:
            try:
                conn.execute(text(\"\"\"
                    CREATE TABLE fidelity_progress (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        client_name VARCHAR(100) NOT NULL,
                        client_phone VARCHAR(20) NOT NULL,
                        staff_name VARCHAR(100) NOT NULL,
                        current_cuts INTEGER NOT NULL DEFAULT 0,
                        last_visit VARCHAR(10),
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE (client_name, client_phone, staff_name)
                    )
                \"\"\"))
                conn.commit()
                print("[Migración] Tabla fidelity_progress creada")
            except Exception as e:
                print(f"[Migración] fidelity_progress: {e}")
        else:
            # Limpiar registros con 0 cortes que puedan existir de ciclos anteriores
            try:
                conn.execute(text("DELETE FROM fidelity_progress WHERE current_cuts <= 0"))
                conn.commit()
            except Exception:
                pass

        # Tabla inactive_days
        if 'inactive_days' not in existing_tables:
            try:
                conn.execute(text(\"\"\"
                    CREATE TABLE inactive_days (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        staff_name VARCHAR(100) NOT NULL,
                        date VARCHAR(10) NOT NULL,
                        reason VARCHAR(200) DEFAULT '',
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE (staff_name, date)
                    )
                \"\"\"))
                conn.commit()
                print("[Migración] Tabla inactive_days creada")
            except Exception as e:
                print(f"[Migración] inactive_days: {e}")

        # Tabla reviews (por si acaso)
        if 'reviews' not in existing_tables:
            try:
                conn.execute(text(\"\"\"
                    CREATE TABLE reviews (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        client_name VARCHAR(100) NOT NULL,
                        rating INTEGER NOT NULL,
                        comment TEXT,
                        staff_name VARCHAR(100),
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                \"\"\"))
                conn.commit()
                print("[Migración] Tabla reviews creada")
            except Exception as e:
                print(f"[Migración] reviews: {e}")
\"\"\"

if migrate_idx != -1:
    content = content[:migrate_idx] + original_migrate

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("__init__.py fully reverted to SQLite logic")
