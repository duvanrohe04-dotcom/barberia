import os

file_path = r'c:\Users\ASUS\OneDrive\Desktop\PAGINAS WEB\barberia\docker-compose.yml'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Cambiar DATABASE_URL de SQLite a PostgreSQL
old_db = "DATABASE_URL=sqlite:////app/instance/barberking.db"
new_db = os.environ.get('DATABASE_URL_POSTGRES', 'DATABASE_URL=postgresql://<user>:<password>@postgres:5432/evolution_db')
content = content.replace(old_db, new_db)

# 2. Asegurar que la web dependa de postgres además de evolution_api
if 'depends_on:' in content:
    # Buscar el bloque depends_on de la web
    # El archivo tiene la estructura:
    # web:
    #   ...
    #   depends_on:
    #     - evolution_api
    
    target_dep = "- evolution_api"
    # Solo reemplazar la primera ocurrencia (la de la web)
    # Buscamos la que está cerca del inicio del archivo
    web_section_end = content.find("evolution_api:")
    web_deps = content[:web_section_end]
    
    if target_dep in web_deps:
        new_deps = "- evolution_api\\n      postgres:\\n        condition: service_healthy"
        web_deps_fixed = web_deps.replace(target_dep, new_deps)
        content = web_deps_fixed + content[web_section_end:]

with open(file_path, 'w', encoding='utf-8') as f:
    # Re-escribir con saltos de línea reales
    f.write(content.replace("\\n", "\\n"))

print("docker-compose.yml updated to use PostgreSQL for the web service")
