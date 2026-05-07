import os

file_path = r'c:\Users\ASUS\OneDrive\Desktop\PAGINAS WEB\barberia\app\routes\main.py'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Asegurar que pasamos tanto config como las variables individuales para base.html
target = "config=conf)"
replacement = "config=conf, config_shop_name=conf['shop_name'], config_shop_logo=conf['shop_logo'])"

if target in content:
    content = content.replace(target, replacement)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("main.py updated with compatibility variables")
else:
    print("Could not find the target code block in main.py")
