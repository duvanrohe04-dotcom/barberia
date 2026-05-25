#!/usr/bin/env python3
"""
Script para migrar datos de SQLite a PostgreSQL
Ejecutar: python migrate_to_postgres.py
"""
import os
import sqlite3
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

# Configuración
SQLITE_PATH = 'instance/barberking.db'
POSTGRES_URL = os.environ.get('DATABASE_URL') or (
    f"postgresql://{os.environ.get('POSTGRES_USER','barber_user')}:{os.environ.get('POSTGRES_PASSWORD','')}@{os.environ.get('POSTGRES_HOST','localhost')}:{os.environ.get('POSTGRES_PORT','5432')}/{os.environ.get('POSTGRES_DB','barberking_db')}"
)

# Tablas a migrar (en orden por foreign keys)
TABLES = [
    'shop_config',
    'services', 
    'staff',
    'admins',
    'appointments',
    'fidelity_progress',
    'inactive_days',
    'reviews'
]

def migrate():
    print(f"Conectando a SQLite: {SQLITE_PATH}")
    sqlite_conn = sqlite3.connect(SQLITE_PATH)
    sqlite_conn.row_factory = sqlite3.Row
    
    print(f"Conectando a PostgreSQL: {POSTGRES_URL}")
    pg_engine = create_engine(POSTGRES_URL)
    
    with pg_engine.connect() as pg_conn:
        for table in TABLES:
            print(f"\nMigrando tabla: {table}")
            
            # Leer datos de SQLite
            cursor = sqlite_conn.execute(f"SELECT * FROM {table}")
            rows = cursor.fetchall()
            
            if not rows:
                print(f"  - Sin datos para migrar")
                continue
            
            # Limpiar tabla en PostgreSQL
            pg_conn.execute(text(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE"))
            
            # Insertar datos
            for row in rows:
                columns = ', '.join(row.keys())
                placeholders = ', '.join([f':{k}' for k in row.keys()])
                query = text(f"INSERT INTO {table} ({columns}) VALUES ({placeholders})")
                pg_conn.execute(query, dict(row))
            
            pg_conn.commit()
            print(f"  - {len(rows)} registros migrados")
    
    sqlite_conn.close()
    print("\nMigración completada!")

if __name__ == '__main__':
    migrate()
