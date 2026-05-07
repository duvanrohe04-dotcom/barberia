import os

file_path = r'c:\Users\ASUS\OneDrive\Desktop\PAGINAS WEB\barberia\docker-compose.yml'

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
found_ports = False
for line in lines:
    if "ports:" in line: found_ports = True
    
    if "command: gunicorn" in line:
        # Limpiar la línea y quitar --preload
        clean_line = line.replace("--preload ", "").replace(" --preload", "")
        new_lines.append(clean_line)
        # Agregar puertos debajo si no existen en el archivo
        if not found_ports:
            indent = line[:line.find("command:")]
            new_lines.append(f"{indent}ports:\\n")
            new_lines.append(f"{indent}  - '80:80'\\n")
    else:
        new_lines.append(line)

with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("docker-compose.yml updated successfully")
