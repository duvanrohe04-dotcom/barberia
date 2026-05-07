import sqlite3
import os

db_path = r'c:\Users\ASUS\OneDrive\Desktop\PAGINAS WEB\barberia\instance\barberking.db'

if not os.path.exists(db_path):
    print(f"Database NOT found at {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

tables = ['admins', 'services', 'staff', 'appointments', 'shop_config']
for table in tables:
    try:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"Table {table}: {count} rows")
        if table == 'shop_config':
            cursor.execute("SELECT key, value FROM shop_config")
            configs = cursor.fetchall()
            for k, v in configs:
                print(f"  {k}: {v}")
    except Exception as e:
        print(f"Table {table}: Error {e}")

conn.close()
