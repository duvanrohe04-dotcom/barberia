import os

file_path = r'c:\Users\ASUS\OneDrive\Desktop\PAGINAS WEB\barberia\app\routes\main.py'

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if 'def index():' in line:
        new_lines.append(line)
        new_lines.append("    from app.models import ShopConfig\n")
    elif 'return render_template(\'index.html\',' in line:
        new_lines.append("    sn = ShopConfig.query.filter_by(key='shop_name').first()\n")
        new_lines.append("    sl = ShopConfig.query.filter_by(key='shop_logo').first()\n")
        new_lines.append("    conf = {'shop_name': sn.value if sn and sn.value else 'BARBERSTYLEPRO', 'shop_logo': sl.value if sl and sl.value else None}\n")
        new_lines.append("    return render_template('index.html',\n")
    elif 'stylists=stylists)' in line:
        new_lines.append("                            stylists=stylists,\n")
        new_lines.append("                            config=conf)\n")
    else:
        new_lines.append(line)

with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
print("File updated successfully")
