import os

file_path = r'c:\Users\ASUS\OneDrive\Desktop\PAGINAS WEB\barberia\app\__init__.py'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Quitar db.create_all() de _migrate_db o capturarlo
content = content.replace("    # 1. Asegurar que las tablas base existan\\n    db.create_all()", "    # 1. Las tablas base se crean en create_app()")
# Por si acaso el comentario es ligeramente diferente o no hay comentario
content = content.replace("    db.create_all()", "    # db.create_all() - movido a create_app()", 1) 

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("__init__.py cleaned up from redundant create_all")
