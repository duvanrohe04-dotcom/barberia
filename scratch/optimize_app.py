import os

file_path = r'c:\Users\ASUS\OneDrive\Desktop\PAGINAS WEB\barberia\app\static\js\app.js'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Optimizar init
old_init = """async function init(){
  // Verificar si hay sesión activa de administrador
  await checkSession();
  
  // Cargar servicios y profesionales en paralelo
  const loaders = [
    loadServices('male'),
    loadServices('female'),
    loadStaff('male'),
    loadStaff('female'),
    loadConfig(),
    loadPublicReviews()
  ];
  
  await Promise.all(loaders);"""

new_init = """async function init(){
  // Cargar todo en paralelo (incluyendo verificación de sesión) para máxima velocidad
  const loaders = [
    checkSession(),
    loadServices('male'),
    loadServices('female'),
    loadStaff('male'),
    loadStaff('female'),
    loadConfig(),
    loadPublicReviews()
  ];
  
  await Promise.all(loaders);"""

if old_init in content:
    content = content.replace(old_init, new_init)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("app.js optimized successfully")
else:
    print("Could not find the target code block in app.js")
