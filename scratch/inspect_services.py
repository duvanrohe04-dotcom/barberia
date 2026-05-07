import sqlite3
import os

db_path = r'c:\Users\ASUS\OneDrive\Desktop\PAGINAS WEB\barberia\instance\barberking.db'

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("--- SERVICIOS ENCONTRADOS ---")
try:
    cursor.execute("SELECT id, name, gender, active, image_url FROM services")
    rows = cursor.fetchall()
    for r in rows:
        print(f"ID: {r[0]} | Nombre: {r[1]} | Género: {r[2]} | Activo: {r[3]} | Imagen: {r[4]}")
except Exception as e:
    print(f"Error: {e}")

print("\n--- CONFIGURACIÓN DE MARCA ---")
try:
    cursor.execute("SELECT key, value FROM shop_config")
    rows = cursor.fetchall()
    for r in rows:
        print(f"Key: {r[0]} | Value: {r[1]}")
except Exception as e:
    print(f"Error: {e}")

conn.close()
