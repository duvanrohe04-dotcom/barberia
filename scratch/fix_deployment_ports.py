import os

# Fix run.py
run_path = r'c:\Users\ASUS\OneDrive\Desktop\PAGINAS WEB\barberia\run.py'
if os.path.exists(run_path):
    with open(run_path, 'r', encoding='utf-8') as f:
        content = f.read()
    content = content.replace("port=81", "port=80")
    with open(run_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("run.py updated to port 80")

# Fix docker-compose.yml
dc_path = r'c:\Users\ASUS\OneDrive\Desktop\PAGINAS WEB\barberia\docker-compose.yml'
if os.path.exists(dc_path):
    with open(dc_path, 'r', encoding='utf-8') as f:
        content = f.read()
    content = content.replace("0.0.0.0:81", "0.0.0.0:80")
    with open(dc_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("docker-compose.yml updated to port 80")
