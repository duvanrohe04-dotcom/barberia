#!/usr/bin/env python3
"""
Script para inicializar la base de datos PostgreSQL
Crea la base de datos 'barberking_db' si no existe
Ejecutar: python setup_postgres.py
"""
import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

def setup_postgres():
    """Crear base de datos PostgreSQL necesaria"""
    
    # URL de conexión al servidor PostgreSQL (sin especificar BD)
    postgres_server_url = 'postgresql://barber_user:barber_pass@localhost:5432/postgres'
    
    print("\n" + "="*60)
    print("🗄️  CONFIGURANDO POSTGRESQL")
    print("="*60)
    
    try:
        # Conectar al servidor (BD por defecto 'postgres')
        engine = create_engine(postgres_server_url)
        
        with engine.connect() as conn:
            # Verificar si la base de datos existe
            result = conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = 'barberking_db'")
            )
            
            if result.fetchone():
                print("\n✅ Base de datos 'barberking_db' ya existe")
            else:
                print("\n📝 Creando base de datos 'barberking_db'...")
                # PostgreSQL requiere AUTOCOMMIT para CREATE DATABASE
                conn = engine.raw_connection()
                conn.set_isolation_level(0)
                cursor = conn.cursor()
                
                try:
                    cursor.execute('CREATE DATABASE barberking_db')
                    conn.commit()
                    print("✅ Base de datos creada exitosamente")
                except Exception as e:
                    if 'already exists' in str(e):
                        print("✅ Base de datos ya existe")
                    else:
                        raise e
                finally:
                    cursor.close()
                    conn.close()
        
        print("\n" + "="*60)
        print("✅ POSTGRESQL LISTO")
        print("="*60)
        print("\nPróximo paso: ejecutar 'python migrate_data_safely.py'")
        print("="*60 + "\n")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nVerifica que PostgreSQL esté ejecutándose:")
        print("  - En Docker: docker-compose up -d postgres")
        print("  - En local: Asegúrate que pg_isready retorne 'accepting connections'")
        return False

if __name__ == '__main__':
    success = setup_postgres()
    sys.exit(0 if success else 1)
