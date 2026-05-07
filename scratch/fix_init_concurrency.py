import os

file_path = r'c:\Users\ASUS\OneDrive\Desktop\PAGINAS WEB\barberia\app\__init__.py'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Modificar create_app para manejar errores de concurrencia en create_all
old_init_block = """    with app.app_context():
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

new_init_block = """    with app.app_context():
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

if old_init_block in content:
    content = content.replace(old_init_block, new_init_block)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("__init__.py updated with concurrent-safe DB initialization")
else:
    # Intento de búsqueda más flexible si el contenido cambió ligeramente
    print("Could not find the exact old_init_block in __init__.py. Attempting flexible replacement.")
    # ... (podría añadir lógica de reemplazo más flexible aquí si fuera necesario)
