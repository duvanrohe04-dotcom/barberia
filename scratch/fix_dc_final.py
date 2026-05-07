import os

file_path = r'c:\Users\ASUS\OneDrive\Desktop\PAGINAS WEB\barberia\docker-compose.yml'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Quitar --preload y agregar puertos
old_line = "command: gunicorn --bind 0.0.0.0:80 --workers 2 --threads 2 --timeout 60 --preload run:app"
new_line = "command: gunicorn --bind 0.0.0.0:80 --workers 2 --threads 2 --timeout 60 run:app\\n    ports:\\n      - \\"80:80\\""

if old_line in content:
    # Usar replace directo con los escapes correctos o simplemente reconstruir
    content = content.replace(old_line, "command: gunicorn --bind 0.0.0.0:80 --workers 2 --threads 2 --timeout 60 run:app\\n    ports:\\n      - \\"80:80\\"")
    # Nota: el script de python escribirá las líneas nuevas correctamente
    content = content.replace("\\n", "\\n") # Asegurar saltos de línea reales
    
    with open(file_path, 'w', encoding='utf-8') as f:
        # Re-escribir con saltos de línea reales
        f.write(content.replace("\\n", "\\n"))
    print("docker-compose.yml updated successfully")
else:
    # Intentar sin el preload por si ya se quitó
    old_line_2 = "command: gunicorn --bind 0.0.0.0:80 --workers 2 --threads 2 --timeout 60 run:app"
    if old_line_2 in content and 'ports:' not in content:
        content = content.replace(old_line_2, old_line_2 + "\\n    ports:\\n      - \\"80:80\\"")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content.replace("\\n", "\\n"))
        print("docker-compose.yml updated successfully (2nd attempt)")
    else:
        print("Could not find the target line in docker-compose.yml")
