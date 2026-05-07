import sqlite3
import os

db_path = r'c:\Users\ASUS\OneDrive\Desktop\PAGINAS WEB\barberia\instance\barberking.db'

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("--- TABLAS EN LA DB ---")
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
for t in tables:
    print(f"Tabla: {t[0]}")

print("\n--- CONTENIDO DE SERVICES ---")
try:
    cursor.execute("SELECT * FROM services")
    rows = cursor.fetchall()
    print(f"Total filas: {len(rows)}")
    for r in rows:
        print(r)
except Exception as e:
    print(f"Error en services: {e}")

conn.close()
