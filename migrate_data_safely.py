#!/usr/bin/env python3
"""
Script para migrar datos de SQLite a PostgreSQL de forma segura
Uso: python migrate_data_safely.py
"""
import os
import sqlite3
import json
from datetime import datetime
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

# Configuración
SQLITE_PATH = 'instance/barberking.db'
POSTGRES_URL = os.environ.get('DATABASE_URL') or (
    f"postgresql://{os.environ.get('POSTGRES_USER','barber_user')}:{os.environ.get('POSTGRES_PASSWORD','')}@{os.environ.get('POSTGRES_HOST','localhost')}:{os.environ.get('POSTGRES_PORT','5432')}/{os.environ.get('POSTGRES_DB','barberking_db')}"
)

def backup_sqlite():
    """Crear backup de la BD SQLite antes de migrar"""
    if not os.path.exists(SQLITE_PATH):
        print(f"⚠️  No se encontró: {SQLITE_PATH}")
        return None
    
    backup_name = f"backup_sqlite_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    import shutil
    shutil.copy(SQLITE_PATH, backup_name)
    print(f"✅ Backup creado: {backup_name}")
    return backup_name

def get_all_tables(conn):
    """Obtener todas las tablas de SQLite"""
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    return [row[0] for row in cursor.fetchall()]

def get_table_schema(sqlite_conn, table_name):
    """Obtener estructura de una tabla SQLite"""
    cursor = sqlite_conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    return cursor.fetchall()

def migrate_table_data(sqlite_conn, pg_engine, table_name):
    """Migrar datos de una tabla SQLite a PostgreSQL"""
    print(f"  📊 Migrando: {table_name}")
    
    # Leer de SQLite
    sqlite_cursor = sqlite_conn.cursor()
    sqlite_cursor.execute(f"SELECT * FROM {table_name}")
    columns = [description[0] for description in sqlite_cursor.description]
    rows = sqlite_cursor.fetchall()
    
    if not rows:
        print(f"    ⓘ Sin datos para migrar")
        return 0
    
    print(f"    📦 Registros encontrados: {len(rows)}")
    
    # Escribir en PostgreSQL
    with pg_engine.connect() as conn:
        # Limpiar tabla en PostgreSQL (sin cascade)
        try:
            conn.execute(text(f"TRUNCATE TABLE {table_name} RESTART IDENTITY"))
            conn.commit()
        except Exception as e:
            print(f"    ⚠️  No se pudo truncate: {e}")
            conn.rollback()
        
        # Insertar datos
        placeholders = ', '.join(['%s'] * len(columns))
        columns_str = ', '.join(columns)
        insert_sql = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"
        
        try:
            for row in rows:
                conn.execute(text(insert_sql), [dict(zip(columns, row))])
            conn.commit()
        except Exception as e:
            print(f"    ❌ Error insertando datos: {e}")
            conn.rollback()
            return 0
    
    print(f"    ✅ {len(rows)} registros migrados")
    return len(rows)

def verify_migration(sqlite_conn, pg_engine, tables):
    """Verificar que la migración fue correcta"""
    print("\n🔍 Verificando migración...")
    
    for table in tables:
        # Contar en SQLite
        sqlite_cursor = sqlite_conn.cursor()
        sqlite_cursor.execute(f"SELECT COUNT(*) FROM {table}")
        sqlite_count = sqlite_cursor.fetchone()[0]
        
        # Contar en PostgreSQL
        with pg_engine.connect() as conn:
            result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
            pg_count = result.scalar()
        
        if sqlite_count == pg_count:
            print(f"  ✅ {table}: {sqlite_count} registros")
        else:
            print(f"  ❌ {table}: SQLite={sqlite_count}, PostgreSQL={pg_count}")

def migrate():
    """Función principal de migración"""
    print("\n" + "="*60)
    print("🚀 INICIO DE MIGRACIÓN DE DATOS")
    print("="*60)
    
    # 1. Verificar que existe SQLite
    if not os.path.exists(SQLITE_PATH):
        print(f"\n❌ Error: Base de datos SQLite no encontrada en {SQLITE_PATH}")
        return False
    
    # 2. Hacer backup
    print("\n📋 Creando backup de seguridad...")
    backup_file = backup_sqlite()
    
    # 3. Conectar a ambas BD
    print("\n🔌 Conectando a bases de datos...")
    try:
        sqlite_conn = sqlite3.connect(SQLITE_PATH)
        print(f"  ✅ SQLite: {SQLITE_PATH}")
        
        pg_engine = create_engine(POSTGRES_URL)
        # Probar conexión
        with pg_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print(f"  ✅ PostgreSQL: Conectado")
    except Exception as e:
        print(f"  ❌ Error de conexión: {e}")
        return False
    
    # 4. Obtener tablas
    print("\n📚 Tablas a migrar...")
    tables = get_all_tables(sqlite_conn)
    tables = [t for t in tables if not t.startswith('sqlite_')]
    for t in tables:
        print(f"  - {t}")
    
    # 5. Migrar cada tabla
    print("\n⚙️  Migrando datos...")
    total_rows = 0
    for table in tables:
        try:
            rows = migrate_table_data(sqlite_conn, pg_engine, table)
            total_rows += rows
        except Exception as e:
            print(f"  ❌ Error en tabla {table}: {e}")
    
    # 6. Verificar
    try:
        verify_migration(sqlite_conn, pg_engine, tables)
    except Exception as e:
        print(f"  ⚠️  Error en verificación: {e}")
    
    # Cerrar conexiones
    sqlite_conn.close()
    
    print("\n" + "="*60)
    print(f"✅ MIGRACIÓN COMPLETADA")
    print(f"   Total de registros migrados: {total_rows}")
    print(f"   Backup guardado en: {backup_file}")
    print("="*60 + "\n")
    
    return True

if __name__ == '__main__':
    success = migrate()
    exit(0 if success else 1)
