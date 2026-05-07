import os

file_path = r'c:\Users\ASUS\OneDrive\Desktop\PAGINAS WEB\barberia\app\__init__.py'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Refactorizar _migrate_db para ser compatible con Postgres y evitar hangs
new_migrate_db = """def _migrate_db():
    \"\"\"Agrega columnas nuevas a tablas existentes de forma segura y compatible con SQLite/PostgreSQL.\"\"\"
    from sqlalchemy import text, inspect
    
    # 1. Asegurar que las tablas base existan
    db.create_all()
    
    inspector = inspect(db.engine)
    
    # Función helper para agregar columnas si no existen
    def add_column_if_missing(table_name, column_name, column_type):
        columns = [c['name'] for c in inspector.get_columns(table_name)]
        if column_name not in columns:
            print(f"[Migración] Agregando columna {column_name} a {table_name}...")
            try:
                with db.engine.connect() as conn:
                    conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"))
                    conn.commit()
                print(f"[Migración] ✅ Columna {column_name} agregada")
            except Exception as e:
                print(f"[Migración] ❌ Error agregando {column_name}: {e}")

    # Lista de columnas a verificar/agregar
    add_column_if_missing('staff', 'phone', 'VARCHAR(20)')
    add_column_if_missing('staff', 'instagram', 'VARCHAR(100)')
    add_column_if_missing('services', 'duration_minutes', 'INTEGER NOT NULL DEFAULT 60')
    add_column_if_missing('appointments', 'duration_minutes', 'INTEGER NOT NULL DEFAULT 60')
    add_column_if_missing('appointments', 'is_free_cut', 'BOOLEAN DEFAULT FALSE')
    add_column_if_missing('appointments', 'gender', "VARCHAR(10) DEFAULT 'male'")
    add_column_if_missing('appointments', 'reminder_sent', 'BOOLEAN DEFAULT FALSE')

    # 3. Inicializar ShopConfig
    from app.models import ShopConfig
    for k in ['shop_name', 'shop_logo', 'wa_sty', 'ig_sty', 'evo_instance']:
        if not ShopConfig.query.filter_by(key=k).first():
            db.session.add(ShopConfig(key=k, value='jsbarbershop' if k=='evo_instance' else ''))
    db.session.commit()

    # 4. Crear tablas críticas con sintaxis compatible
    existing_tables = inspector.get_table_names()
    is_postgres = db.engine.url.drivername.startswith('postgresql')
    id_type = "SERIAL PRIMARY KEY" if is_postgres else "INTEGER PRIMARY KEY AUTOINCREMENT"

    with db.engine.connect() as conn:
        if 'fidelity_progress' not in existing_tables:
            try:
                conn.execute(text(f\"\"\"
                    CREATE TABLE fidelity_progress (
                        id {id_type},
                        client_name VARCHAR(100) NOT NULL,
                        client_phone VARCHAR(20) NOT NULL,
                        staff_name VARCHAR(100) NOT NULL,
                        current_cuts INTEGER NOT NULL DEFAULT 0,
                        last_visit VARCHAR(10),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE (client_name, client_phone, staff_name)
                    )
                \"\"\"))
                conn.commit()
            except Exception as e: print(f"[Migración] Error fidelity_progress: {e}")

        if 'inactive_days' not in existing_tables:
            try:
                conn.execute(text(f\"\"\"
                    CREATE TABLE inactive_days (
                        id {id_type},
                        staff_name VARCHAR(100) NOT NULL,
                        date VARCHAR(10) NOT NULL,
                        reason VARCHAR(200) DEFAULT '',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE (staff_name, date)
                    )
                \"\"\"))
                conn.commit()
            except Exception as e: print(f"[Migración] Error inactive_days: {e}")

        if 'reviews' not in existing_tables:
            try:
                conn.execute(text(f\"\"\"
                    CREATE TABLE reviews (
                        id {id_type},
                        client_name VARCHAR(100) NOT NULL,
                        rating INTEGER NOT NULL,
                        comment TEXT,
                        staff_name VARCHAR(100),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                \"\"\"))
                conn.commit()
            except Exception as e: print(f"[Migración] Error reviews: {e}")
"""

# Encontrar el inicio de _migrate_db y reemplazar hasta el final
start_marker = "def _migrate_db():"
start_idx = content.find(start_marker)
if start_idx != -1:
    content = content[:start_idx] + new_migrate_db
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("__init__.py updated with robust migration logic")
else:
    print("Could not find _migrate_db in __init__.py")
